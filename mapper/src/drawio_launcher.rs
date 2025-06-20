/// Launches draw.io in the default web browser, preloading the given compressed XML fragment.
///
/// # Arguments
/// * `compressed_xml` - The compressed, base64, urlencoded XML string for draw.io
pub fn launch_drawio_with_xml(compressed_xml: &str) -> Result<(), String> {
    let url = format!("https://app.diagrams.net/?splash=0&libs=general;uml#R{compressed_xml}");
    webbrowser::open(&url).map_err(|e| format!("Failed to open browser: {e}"))?;
    Ok(())
}
