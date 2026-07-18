use keyring::v1::{Entry, Error as KeyringError};
use std::net::IpAddr;
use url::Url;

const KEYCHAIN_SERVICE: &str = "com.pentagon5.desktop";
const TOKEN_ACCOUNT: &str = "auth-token";
const DEVICE_ACCOUNT: &str = "device-key";

fn keychain_entry(account: &str) -> Result<Entry, String> {
    Entry::new(KEYCHAIN_SERVICE, account).map_err(|error| error.to_string())
}

fn new_device_key() -> String {
    format!("desktop-{}", uuid::Uuid::new_v4())
}

#[tauri::command]
fn store_auth_token(token: String) -> Result<(), String> {
    if token.len() < 32 || token.len() > 16_384 {
        return Err("Invalid opaque token length".into());
    }
    keychain_entry(TOKEN_ACCOUNT)?
        .set_password(&token)
        .map_err(|error| error.to_string())
}

#[tauri::command]
fn load_auth_token() -> Result<Option<String>, String> {
    match keychain_entry(TOKEN_ACCOUNT)?.get_password() {
        Ok(token) => Ok(Some(token)),
        Err(KeyringError::NoEntry) => Ok(None),
        Err(error) => Err(error.to_string()),
    }
}

#[tauri::command]
fn delete_auth_token() -> Result<(), String> {
    match keychain_entry(TOKEN_ACCOUNT)?.delete_credential() {
        Ok(()) | Err(KeyringError::NoEntry) => Ok(()),
        Err(error) => Err(error.to_string()),
    }
}

#[tauri::command]
fn get_or_create_device_key() -> Result<String, String> {
    let entry = keychain_entry(DEVICE_ACCOUNT)?;
    match entry.get_password() {
        Ok(device_key) if (8..=200).contains(&device_key.len()) => Ok(device_key),
        Ok(_) | Err(KeyringError::NoEntry) => {
            let device_key = new_device_key();
            entry
                .set_password(&device_key)
                .map_err(|error| error.to_string())?;
            Ok(device_key)
        }
        Err(error) => Err(error.to_string()),
    }
}

fn is_loopback(host: &str) -> bool {
    host.eq_ignore_ascii_case("localhost")
        || host
            .parse::<IpAddr>()
            .is_ok_and(|address| address.is_loopback())
}

fn is_trusted_web_url(url: &Url) -> bool {
    url.username().is_empty()
        && url.password().is_none()
        && url.host_str().is_some_and(|host| {
            url.scheme() == "https" || (url.scheme() == "http" && is_loopback(host))
        })
}

fn validate_oidc_authorization_url(value: &str) -> Result<Url, String> {
    let url = Url::parse(value).map_err(|_| "Invalid authorization URL")?;
    if !is_trusted_web_url(&url) {
        return Err("Authorization URL must use HTTPS (or loopback HTTP)".into());
    }

    let single_parameter = |name: &str| {
        let mut values = url
            .query_pairs()
            .filter_map(|(key, value)| (key == name).then(|| value.into_owned()));
        let first = values.next()?;
        if first.is_empty() || values.next().is_some() {
            None
        } else {
            Some(first)
        }
    };
    let redirect_uri =
        single_parameter("redirect_uri").ok_or("Authorization URL has no redirect URI")?;
    let redirect = Url::parse(&redirect_uri).map_err(|_| "Invalid provider redirect URI")?;
    if !is_trusted_web_url(&redirect)
        || redirect.path() != "/v1/auth/oidc/callback"
        || redirect.query().is_some()
        || redirect.fragment().is_some()
    {
        return Err("Provider redirect URI is not an approved backend callback".into());
    }
    if single_parameter("response_type").as_deref() != Some("code")
        || single_parameter("client_id").is_none()
        || single_parameter("state").is_none()
        || single_parameter("code_challenge").is_none()
        || single_parameter("code_challenge_method").as_deref() != Some("S256")
    {
        return Err("Authorization URL is not an approved desktop OIDC request".into());
    }
    Ok(url)
}

#[tauri::command]
fn open_oidc_login(authorization_url: String) -> Result<(), String> {
    let url = validate_oidc_authorization_url(&authorization_url)?;
    open::that_detached(url.as_str()).map_err(|error| error.to_string())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_deep_link::init())
        .invoke_handler(tauri::generate_handler![
            store_auth_token,
            load_auth_token,
            delete_auth_token,
            get_or_create_device_key,
            open_oidc_login
        ])
        .run(tauri::generate_context!())
        .expect("failed to run Pentagon 5 desktop");
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn permits_https_oidc_code_flow() {
        let value = concat!(
            "https://identity.example.test/authorize?",
            "response_type=code&client_id=desktop&state=random&",
            "code_challenge=challenge&code_challenge_method=S256&",
            "redirect_uri=https%3A%2F%2Fapi.example.test%2Fv1%2Fauth%2Foidc%2Fcallback"
        );
        assert!(validate_oidc_authorization_url(value).is_ok());
    }

    #[test]
    fn creates_bounded_random_device_keys() {
        let first = new_device_key();
        let second = new_device_key();
        assert!((8..=200).contains(&first.len()));
        assert!(first.starts_with("desktop-"));
        assert_ne!(first, second);
    }

    #[test]
    fn permits_loopback_http_for_local_identity_provider() {
        let value = concat!(
            "http://127.0.0.1:9000/authorize?",
            "response_type=code&client_id=desktop&state=random&",
            "code_challenge=challenge&code_challenge_method=S256&",
            "redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fv1%2Fauth%2Foidc%2Fcallback"
        );
        assert!(validate_oidc_authorization_url(value).is_ok());
    }

    #[test]
    fn rejects_generic_or_malformed_urls() {
        for value in [
            "file:///tmp/token",
            "https://example.test/",
            "http://identity.example.test/authorize?response_type=code",
            "https://identity.example.test/authorize?response_type=code&client_id=x&state=y&code_challenge=z&code_challenge_method=plain&redirect_uri=https%3A%2F%2Fapi.example.test%2Fv1%2Fauth%2Foidc%2Fcallback",
            "https://identity.example.test/authorize?response_type=code&client_id=x&state=y&code_challenge=z&code_challenge_method=S256&redirect_uri=pentagon5%3A%2F%2Fauth%2Fcallback",
            "https://identity.example.test/authorize?response_type=code&client_id=x&state=y&code_challenge=z&code_challenge_method=S256&redirect_uri=http%3A%2F%2Fapi.example.test%2Fv1%2Fauth%2Foidc%2Fcallback",
            "https://identity.example.test/authorize?response_type=code&client_id=x&state=y&state=duplicate&code_challenge=z&code_challenge_method=S256&redirect_uri=https%3A%2F%2Fapi.example.test%2Fv1%2Fauth%2Foidc%2Fcallback",
        ] {
            assert!(validate_oidc_authorization_url(value).is_err(), "{value}");
        }
    }
}
