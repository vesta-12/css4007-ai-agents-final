// Executed by macOS JavaScript for Automation, once at server startup.
ObjC.import("AppKit");

function run() {
  const names = {
    inbox: "tray", papers: "doc.on.doc", doc: "doc.text", grid: "tablecells",
    spread: "minus.circle", search: "magnifyingglass", panel: "sidebar.right",
    play: "play.fill", arrow: "chevron.right", close: "xmark"
  };
  const symbols = {};
  for (const id of Object.keys(names)) {
    const image = $.NSImage.imageWithSystemSymbolNameAccessibilityDescription(names[id], $());
    if (!image || image.isNil()) continue;
    const config = $.NSImageSymbolConfiguration.configurationWithPointSizeWeight(42, $.NSFontWeightRegular);
    const rep = $.NSBitmapImageRep.imageRepWithData(image.imageWithSymbolConfiguration(config).TIFFRepresentation);
    const png = rep.representationUsingTypeProperties($.NSBitmapImageFileTypePNG, $.NSDictionary.dictionary);
    symbols[id] = ObjC.unwrap(png.base64EncodedStringWithOptions(0));
  }
  return JSON.stringify(symbols);
}
