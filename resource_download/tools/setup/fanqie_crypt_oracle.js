/**
 * Frida RPC — com.dragon.read CryptManager.decrypt + gunzip
 * exports: ping, decrypt, maxKeyVersion
 */
'use strict';

function gunzipToString(bytes) {
  var GZIPInputStream = Java.use('java.util.zip.GZIPInputStream');
  var ByteArrayInputStream = Java.use('java.io.ByteArrayInputStream');
  var InputStreamReader = Java.use('java.io.InputStreamReader');
  var BufferedReader = Java.use('java.io.BufferedReader');
  var StringBuilder = Java.use('java.lang.StringBuilder');
  var br = BufferedReader.$new(
    InputStreamReader.$new(GZIPInputStream.$new(ByteArrayInputStream.$new(bytes)), 'UTF-8')
  );
  var sb = StringBuilder.$new();
  var line;
  while ((line = br.readLine()) !== null) {
    sb.append(line);
    sb.append('\n');
  }
  br.close();
  return '' + sb.toString();
}

function headHex(bytes, n) {
  n = n || 8;
  var out = [];
  for (var i = 0; i < Math.min(n, bytes.length); i++) {
    var b = bytes[i];
    if (b < 0) b += 256;
    out.push(('0' + b.toString(16)).slice(-2));
  }
  return out.join('');
}

rpc.exports = {
  ping: function () {
    return 'pong';
  },

  maxKeyVersion: function () {
    return new Promise(function (resolve) {
      Java.perform(function () {
        try {
          var CM = Java.use('com.dragon.read.crypt.CryptManager');
          resolve({ ok: true, version: CM.getMaxMetaKeyVersion() });
        } catch (e) {
          resolve({ ok: false, error: '' + e });
        }
      });
    });
  },

  /**
   * @param {string} cipherB64
   * @param {string} keyB64
   * @param {number} keyVersion
   */
  decrypt: function (cipherB64, keyB64, keyVersion) {
    return new Promise(function (resolve) {
      Java.perform(function () {
        try {
          var CM = Java.use('com.dragon.read.crypt.CryptManager');
          var Base64 = Java.use('android.util.Base64');
          var ver = parseInt(keyVersion, 10) || 0;
          var out = CM.decrypt(cipherB64, keyB64, ver);
          var outB64 = Base64.encodeToString(out, 2); // NO_WRAP
          var hx = headHex(out, 8);
          var text = null;
          var gunzipErr = null;
          if (hx.indexOf('1f8b') === 0) {
            try {
              text = gunzipToString(out);
            } catch (e) {
              gunzipErr = '' + e;
            }
          } else {
            gunzipErr = 'not gzip head=' + hx;
          }
          resolve({
            ok: true,
            out_len: out.length,
            out_head_hex: hx,
            out_b64: outB64,
            gzip: hx.indexOf('1f8b') === 0,
            text: text,
            gunzip_err: gunzipErr,
            key_version: ver,
          });
        } catch (e) {
          resolve({ ok: false, error: '' + e });
        }
      });
    });
  },
};
