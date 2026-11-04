/* Slide Vault — minimal ZIP reader/writer built on native CompressionStream.
 * Zero dependencies: reads and writes .pptx-compatible ZIP archives entirely
 * in the browser, so files never leave the device.
 *
 * Exposes window.PPTXLite = { readZIP, writeZIP }.
 * In Node (tests): require() this file -> module.exports = same API.
 */
(function () {
  "use strict";

  if (typeof CompressionStream === "undefined" || typeof DecompressionStream === "undefined") {
    var stub = null;
    if (typeof window !== "undefined") window.PPTXLite = stub;
    return;
  }

  var CRC_TABLE = (function () {
    var t = new Uint32Array(256);
    for (var n = 0; n < 256; n++) {
      var c = n;
      for (var k = 0; k < 8; k++) c = (c & 1) ? (0xEDB88320 ^ (c >>> 1)) : (c >>> 1);
      t[n] = c >>> 0;
    }
    return t;
  })();

  function crc32(u8) {
    var c = 0xFFFFFFFF;
    for (var i = 0; i < u8.length; i++) c = CRC_TABLE[(c ^ u8[i]) & 0xFF] ^ (c >>> 8);
    return (c ^ 0xFFFFFFFF) >>> 0;
  }

  async function inflate(data) {
    var stream = new Blob([data]).stream().pipeThrough(new DecompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  async function deflate(data) {
    var stream = new Blob([data]).stream().pipeThrough(new CompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }

  /* Read a ZIP buffer -> [{ name, data:Uint8Array }, ...] (directories skipped). */
  async function readZIP(buffer) {
    var u8 = new Uint8Array(buffer);
    var dv = new DataView(buffer);
    var eocd = -1;
    for (var i = u8.length - 22; i >= Math.max(0, u8.length - 22 - 65536); i--) {
      if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
    }
    if (eocd < 0) throw new Error("Not a valid .pptx (ZIP) file");
    var count = dv.getUint16(eocd + 10, true);
    var cdOff = dv.getUint32(eocd + 16, true);
    if (count === 0xFFFF || cdOff === 0xFFFFFFFF) throw new Error("ZIP64 archives are not supported");
    var pending = [];
    var p = cdOff;
    for (var e = 0; e < count; e++) {
      if (p + 46 > u8.length || dv.getUint32(p, true) !== 0x02014b50)
        throw new Error("Corrupt ZIP central directory");
      var flags = dv.getUint16(p + 8, true);
      var method = dv.getUint16(p + 10, true);
      var csize = dv.getUint32(p + 20, true);
      var nameLen = dv.getUint16(p + 28, true);
      var extraLen = dv.getUint16(p + 30, true);
      var commentLen = dv.getUint16(p + 32, true);
      var localOff = dv.getUint32(p + 42, true);
      var name = new TextDecoder().decode(u8.subarray(p + 46, p + 46 + nameLen));
      p += 46 + nameLen + extraLen + commentLen;
      if (flags & 0x1) throw new Error("Password-protected files are not supported");
      if (name.endsWith("/")) continue;
      var lNameLen = dv.getUint16(localOff + 26, true);
      var lExtraLen = dv.getUint16(localOff + 28, true);
      var start = localOff + 30 + lNameLen + lExtraLen;
      pending.push({ name: name, method: method, comp: u8.subarray(start, start + csize) });
    }
    await Promise.all(pending.map(async function (en) {
      if (en.method === 0) en.data = en.comp;
      else if (en.method === 8) en.data = await inflate(en.comp);
      else throw new Error("Unsupported ZIP compression method");
      delete en.comp;
      delete en.method;
    }));
    return pending;
  }

  /* Write entries [{ name, data:Uint8Array }] -> Blob (.pptx-flavoured ZIP). */
  async function writeZIP(entries) {
    var enc = new TextEncoder();
    var chunks = [];
    var central = [];
    var offset = 0;
    var STORE = /\.(png|jpe?g|gif|webp|bmp|tiff?|mp4|m4v|mov|avi|wmv|mp3|wav|m4a|woff2?|ttf|otf|eot)$/i;
    for (var i = 0; i < entries.length; i++) {
      var name = enc.encode(entries[i].name);
      var data = entries[i].data;
      var crc = crc32(data);
      var method = 8;
      var out = data;
      if (!STORE.test(entries[i].name)) {
        var smaller = await deflate(data);
        if (smaller.length < data.length) out = smaller;
        else method = 0;
      } else {
        method = 0;
      }
      var local = new Uint8Array(30 + name.length);
      var ldv = new DataView(local.buffer);
      ldv.setUint32(0, 0x04034b50, true);
      ldv.setUint16(4, 20, true);
      ldv.setUint16(6, 0x0800, true);        // UTF-8 file names
      ldv.setUint16(8, method, true);
      ldv.setUint32(14, crc, true);
      ldv.setUint32(18, out.length, true);
      ldv.setUint32(22, data.length, true);
      ldv.setUint16(26, name.length, true);
      local.set(name, 30);
      chunks.push(local, out);

      var cen = new Uint8Array(46 + name.length);
      var cdv = new DataView(cen.buffer);
      cdv.setUint32(0, 0x02014b50, true);
      cdv.setUint16(4, 20, true);
      cdv.setUint16(6, 20, true);
      cdv.setUint16(8, 0x0800, true);
      cdv.setUint16(10, method, true);
      cdv.setUint32(16, crc, true);
      cdv.setUint32(20, out.length, true);
      cdv.setUint32(24, data.length, true);
      cdv.setUint16(28, name.length, true);
      cdv.setUint32(42, offset, true);
      cen.set(name, 46);
      central.push(cen);

      offset += local.length + out.length;
    }
    var cdStart = offset;
    var cdSize = 0;
    for (var j = 0; j < central.length; j++) cdSize += central[j].length;
    var eocd = new Uint8Array(22);
    var edv = new DataView(eocd.buffer);
    edv.setUint32(0, 0x06054b50, true);
    edv.setUint16(8, entries.length, true);
    edv.setUint16(10, entries.length, true);
    edv.setUint32(12, cdSize, true);
    edv.setUint32(16, cdStart, true);
    return new Blob(chunks.concat(central, [eocd]),
      { type: "application/vnd.openxmlformats-officedocument.presentationml.presentation" });
  }

  var api = { readZIP: readZIP, writeZIP: writeZIP, crc32: crc32 };
  if (typeof window !== "undefined") window.PPTXLite = api;
  else if (typeof module !== "undefined" && module.exports) module.exports = api;
  else globalThis.PPTXLite = api;
})();
