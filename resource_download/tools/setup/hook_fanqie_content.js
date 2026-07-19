/**
 * 第二套：CryptManager + DecryptKey + TextView 长中文；无全局 String/GZIP。
 */
'use strict';

function looksLikeNovelText(s) {
  if (!s || s.length < 40) return false;
  var cn = 0;
  var n = Math.min(s.length, 400);
  for (var i = 0; i < n; i++) {
    var c = s.charCodeAt(i);
    if (c >= 0x4e00 && c <= 0x9fff) cn++;
  }
  return cn >= 12;
}

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
    return out.join('') + (arr.length > n ? '...' : '') + ' len=' + arr.length;
  } catch (e) {
    return '<bytes err>';
  }
}

function sendHit(tag, payload) {
  send({ t: 'hit', tag: tag, p: payload, ts: Date.now() });
}

function hookAllOverloads(cls, methodName, tag) {
  try {
    if (!cls[methodName]) return 0;
    var n = 0;
    cls[methodName].overloads.forEach(function (ov) {
      ov.implementation = function () {
        var args = [];
        for (var i = 0; i < arguments.length; i++) {
          var a = arguments[i];
          if (a && a.length !== undefined && typeof a !== 'string') {
            try { args.push(bytesPreview(a, 20)); } catch (e) { args.push(safeStr(a, 40)); }
          } else {
            args.push(safeStr(a, 160));
          }
        }
        var ret = ov.apply(this, arguments);
        var rs = safeStr(ret, 1000);
        sendHit(tag + '.' + methodName, { args: args, ret: rs });
        return ret;
      };
      n++;
    });
    return n;
  } catch (e) {
    send({ t: 'log', msg: 'hook fail ' + tag + '.' + methodName + ': ' + e });
    return 0;
  }
}

function hookClassAllInteresting(cn, forceAll) {
  try {
    var cls = Java.use(cn);
    var methods = cls.class.getDeclaredMethods();
    var seen = {};
    var n = 0;
    for (var i = 0; i < methods.length; i++) {
      var mn = methods[i].getName();
      if (seen[mn]) continue;
      if (/^toString$|^hashCode$|^equals$|^wait$|^notify|^getClass$/.test(mn)) continue;
      if (!forceAll && !/decrypt|decode|crypt|content|key|parse|uncompress|inflate|getText|set|process/i.test(mn)) {
        // CryptManager / DecryptKey 强制全挂（除噪声）
        if (cn.indexOf('CryptManager') === -1 && cn.indexOf('DecryptKey') === -1) continue;
      }
      seen[mn] = true;
      n += hookAllOverloads(cls, mn, cn);
    }
    send({ t: 'log', msg: 'hooked ' + cn + ' methods~' + n });
    return n;
  } catch (e) {
    send({ t: 'log', msg: 'class miss ' + cn + ': ' + e });
    return 0;
  }
}

function hookCipherLight() {
  try {
    var Cipher = Java.use('javax.crypto.Cipher');
    Cipher.doFinal.overload('[B').implementation = function (input) {
      var out = this.doFinal(input);
      try {
        if (input && input.length >= 200) {
          var text = '';
          try { text = Java.use('java.lang.String').$new(out, 'UTF-8'); } catch (e) {}
          sendHit('Cipher.doFinal', {
            algo: '' + this.getAlgorithm(),
            in_len: input.length,
            out_len: out ? out.length : 0,
            out_head: bytesPreview(out, 8),
            text_head: safeStr(text, 500),
          });
        }
      } catch (e) {}
      return out;
    };
    send({ t: 'log', msg: 'hooked Cipher.doFinal (>=200)' });
  } catch (e) {
    send({ t: 'log', msg: 'Cipher fail: ' + e });
  }
}

function hookJSONContent() {
  try {
    var JSONObject = Java.use('org.json.JSONObject');
    JSONObject.optString.overload('java.lang.String').implementation = function (key) {
      var v = this.optString(key);
      if ((key === 'content' || key === 'text' || key === 'body') && v && v.length > 80) {
        sendHit('JSON.optString(' + key + ')', { len: v.length, head: safeStr(v, 120) });
      }
      return v;
    };
    send({ t: 'log', msg: 'hooked JSONObject.optString' });
  } catch (e) {}
}

function hookTextView() {
  try {
    var TV = Java.use('android.widget.TextView');
    TV.setText.overload('java.lang.CharSequence').implementation = function (cs) {
      try {
        var s = cs ? ('' + cs) : '';
        if (looksLikeNovelText(s) && s.length >= 80) {
          sendHit('TextView.setText', { len: s.length, text: safeStr(s, 800) });
        }
      } catch (e) {}
      return this.setText(cs);
    };
    send({ t: 'log', msg: 'hooked TextView.setText (long Chinese only)' });
  } catch (e) {
    send({ t: 'log', msg: 'TextView fail: ' + e });
  }
}

function coreHooks() {
  hookCipherLight();
  hookJSONContent();
  hookTextView();
  [
    'com.dragon.read.crypt.CryptManager',
    'com.dragon.read.reader.DecryptKey',
  ].forEach(function (cn) {
    hookClassAllInteresting(cn, true);
  });
}

function delayedScan() {
  setTimeout(function () {
    Java.perform(function () {
      send({ t: 'log', msg: 'delayed re-hook + scan' });
      coreHooks();
      var hits = [];
      try {
        Java.enumerateLoadedClasses({
          onMatch: function (name) {
            if (name.indexOf('com.dragon.read') !== 0) return;
            if (/Decrypt|decrypt|CryptManager|ChapterContent|ReaderContent|ContentCodec|NovelContent/i.test(name) &&
                name.indexOf('$') === -1) {
              hits.push(name);
            }
          },
          onComplete: function () {
            send({ t: 'classes', count: hits.length, names: hits.slice(0, 50) });
            hits.slice(0, 20).forEach(function (cn) {
              hookClassAllInteresting(cn, true);
            });
          },
        });
      } catch (e) {
        send({ t: 'log', msg: 'scan fail: ' + e });
      }
    });
  }, 12000);
}

Java.perform(function () {
  send({ t: 'log', msg: 'hook set v2: CryptManager+DecryptKey+TextView' });
  coreHooks();
  send({ t: 'ready', msg: 'hooks ready — open book, enter chapter, then NEXT chapter' });
  delayedScan();
});
