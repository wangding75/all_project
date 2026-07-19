/**
 * 完整 dump CryptManager.decrypt 入参/出参到设备文件，并枚举算法相关方法。
 */
'use strict';

var DUMP_DIR = '/data/local/tmp/fq_crypt';
var seq = 0;

function safeStr(o, maxLen) {
  maxLen = maxLen || 200;
  try {
    if (o === null || o === undefined) return 'null';
    var s = '' + o;
    if (s.length > maxLen) return s.slice(0, maxLen) + '...(' + s.length + ')';
    return s;
  } catch (e) {
    return '<err>';
  }
}

function ensureDir() {
  try {
    var File = Java.use('java.io.File');
    var d = File.$new(DUMP_DIR);
    if (!d.exists()) d.mkdirs();
  } catch (e) {
    send({ t: 'log', msg: 'mkdir fail: ' + e });
  }
}

function writeBytes(path, bytes) {
  var FileOutputStream = Java.use('java.io.FileOutputStream');
  var fos = FileOutputStream.$new(path);
  fos.write(bytes);
  fos.close();
}

function writeText(path, text) {
  var FileOutputStream = Java.use('java.io.FileOutputStream');
  var jstr = Java.use('java.lang.String').$new(text);
  var fos = FileOutputStream.$new(path);
  fos.write(jstr.getBytes('UTF-8'));
  fos.close();
}

function bytesToB64(bytes) {
  return Java.use('android.util.Base64').encodeToString(bytes, 2); // NO_WRAP
}

function inspectCryptManager() {
  try {
    var cls = Java.use('com.dragon.read.crypt.CryptManager');
    var methods = cls.class.getDeclaredMethods();
    var ms = [];
    for (var i = 0; i < methods.length; i++) {
      ms.push('' + methods[i]);
    }
    send({ t: 'methods', cls: 'CryptManager', methods: ms });
    // fields
    var fields = cls.class.getDeclaredFields();
    var fs = [];
    for (var j = 0; j < fields.length; j++) {
      fs.push('' + fields[j]);
    }
    send({ t: 'fields', cls: 'CryptManager', fields: fs });
  } catch (e) {
    send({ t: 'log', msg: 'inspect CM fail: ' + e });
  }
  try {
    var dk = Java.use('com.dragon.read.reader.DecryptKey');
    var methods2 = dk.class.getDeclaredMethods();
    var ms2 = [];
    for (var k = 0; k < methods2.length; k++) ms2.push('' + methods2[k]);
    send({ t: 'methods', cls: 'DecryptKey', methods: ms2 });
  } catch (e) {
    send({ t: 'log', msg: 'inspect DK fail: ' + e });
  }
}

function hookDecrypt() {
  var CM = Java.use('com.dragon.read.crypt.CryptManager');
  // 尽量挂所有 decrypt 重载
  var ovs = CM.decrypt.overloads;
  send({ t: 'log', msg: 'CryptManager.decrypt overloads=' + ovs.length });
  ovs.forEach(function (ov, idx) {
    ov.implementation = function () {
      var ret = ov.apply(this, arguments);
      try {
        seq += 1;
        var id = ('0000' + seq).slice(-4);
        var prefix = DUMP_DIR + '/' + id;
        ensureDir();

        var meta = {
          id: id,
          overload: idx,
          argc: arguments.length,
          args: [],
        };

        for (var i = 0; i < arguments.length; i++) {
          var a = arguments[i];
          if (a === null || a === undefined) {
            meta.args.push({ i: i, type: 'null' });
            continue;
          }
          var tname = '' + (a.$className || typeof a);
          // byte[]
          if (a.length !== undefined && typeof a !== 'string' && tname.indexOf('String') === -1) {
            try {
              var path = prefix + '_arg' + i + '.bin';
              writeBytes(path, a);
              meta.args.push({
                i: i,
                type: 'byte[]',
                len: a.length,
                path: path,
                head_hex: bytesPreview(a, 16),
                b64_head: safeStr(bytesToB64(a), 80),
              });
              continue;
            } catch (e1) {}
          }
          // String
          var s = '' + a;
          if (s.length > 64) {
            writeText(prefix + '_arg' + i + '.txt', s);
            meta.args.push({
              i: i,
              type: 'String',
              len: s.length,
              path: prefix + '_arg' + i + '.txt',
              head: s.slice(0, 80),
            });
          } else {
            meta.args.push({ i: i, type: 'String/other', value: s });
          }
        }

        if (ret) {
          try {
            // byte[] return
            if (ret.length !== undefined && typeof ret !== 'string') {
              writeBytes(prefix + '_out.bin', ret);
              meta.out = {
                type: 'byte[]',
                len: ret.length,
                path: prefix + '_out.bin',
                head_hex: bytesPreview(ret, 16),
                gzip: bytesPreview(ret, 2) === '1f8b',
              };
              // 同步 gunzip 到 txt（便于直接看）
              try {
                var GZIPInputStream = Java.use('java.util.zip.GZIPInputStream');
                var ByteArrayInputStream = Java.use('java.io.ByteArrayInputStream');
                var ByteArrayOutputStream = Java.use('java.io.ByteArrayOutputStream');
                var bis = ByteArrayInputStream.$new(ret);
                var gis = GZIPInputStream.$new(bis);
                var bos = ByteArrayOutputStream.$new();
                var buf = Java.array('byte', [0, 0, 0, 0, 0, 0, 0, 0]);
                // use larger buffer via Java
                var buf2 = Java.use('java.lang.reflect.Array').newInstance(
                  Java.use('java.lang.Byte').TYPE, 8192
                );
                // simpler: BufferedReader
                var isr = Java.use('java.io.InputStreamReader').$new(gis, 'UTF-8');
                var br = Java.use('java.io.BufferedReader').$new(isr);
                var sb = Java.use('java.lang.StringBuilder').$new();
                var line;
                while ((line = br.readLine()) !== null) {
                  sb.append(line);
                  sb.append('\n');
                }
                br.close();
                var plain = '' + sb.toString();
                writeText(prefix + '_out.html', plain);
                meta.out.html_path = prefix + '_out.html';
                meta.out.html_len = plain.length;
                meta.out.html_head = plain.slice(0, 120);
              } catch (gzErr) {
                meta.out.gunzip_err = '' + gzErr;
              }
            } else {
              var rs = '' + ret;
              writeText(prefix + '_out.txt', rs);
              meta.out = { type: 'String', len: rs.length, path: prefix + '_out.txt', head: rs.slice(0, 120) };
            }
          } catch (e2) {
            meta.out_err = '' + e2;
          }
        }

        writeText(prefix + '_meta.json', JSON.stringify(meta));
        // 精简 meta 上报（大文件已在设备上）
        send({
          t: 'dump',
          meta: {
            id: meta.id,
            argc: meta.argc,
            out: meta.out,
            args_summary: meta.args.map(function (x) {
              return { i: x.i, type: x.type, len: x.len, value: x.value, head: x.head };
            }),
          },
        });
      } catch (e) {
        send({ t: 'log', msg: 'dump fail: ' + e });
      }
      return ret;
    };
  });
  send({ t: 'log', msg: 'hooked all CryptManager.decrypt' });
}

function bytesPreview(arr, n) {
  n = n || 16;
  try {
    var out = [];
    var len = Math.min(arr.length, n);
    for (var i = 0; i < len; i++) {
      var b = arr[i];
      if (b < 0) b += 256;
      out.push(('0' + b.toString(16)).slice(-2));
    }
    return out.join('');
  } catch (e) {
    return '';
  }
}

function hookDecryptKeyGetters() {
  try {
    var DK = Java.use('com.dragon.read.reader.DecryptKey');
    ['f', 'b', 'c', 'd', 'e', 'a'].forEach(function (mn) {
      try {
        if (!DK[mn]) return;
        DK[mn].overloads.forEach(function (ov) {
          ov.implementation = function () {
            var r = ov.apply(this, arguments);
            // 低频：只记前几次 key 变化
            send({ t: 'key', method: mn, ret: safeStr(r, 200) });
            return r;
          };
        });
        send({ t: 'log', msg: 'hook DecryptKey.' + mn });
      } catch (e) {}
    });
  } catch (e) {
    send({ t: 'log', msg: 'DecryptKey hook fail: ' + e });
  }
}

Java.perform(function () {
  ensureDir();
  inspectCryptManager();
  hookDecrypt();
  hookDecryptKeyGetters();
  send({ t: 'ready', msg: 'dump hooks ready — open new chapters' });
});
