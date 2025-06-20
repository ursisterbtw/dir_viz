use std::io::Write;

/// Compresses XML using DEFLATE (raw, no zlib header), then base64 and URL-safe encodes for draw.io
pub fn compress_and_encode(xml: &str) -> Result<String, String> {
    use base64::{Engine as _, engine::general_purpose};
    use flate2::Compression;
    use flate2::write::DeflateEncoder;
    use urlencoding::encode;

    // Compress with raw DEFLATE
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::default());
    encoder
        .write_all(xml.as_bytes())
        .map_err(|e| e.to_string())?;
    let compressed = encoder.finish().map_err(|e| e.to_string())?;

    // Standard base64 encode (draw.io expects standard, not URL-safe)
    let b64 = general_purpose::STANDARD.encode(&compressed);

    // URL-encode (draw.io expects percent-encoded)
    Ok(encode(&b64).to_string())
}
