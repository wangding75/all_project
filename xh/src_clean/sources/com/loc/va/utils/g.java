package com.loc.va.utils;

import android.icu.lang.UCharacter;
import android.os.ParcelUuid;
import android.util.ArrayMap;
import android.util.Log;
import android.util.SparseArray;
import b.k0;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Iterator;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class g {

    /* renamed from: i, reason: collision with root package name */
    private static final int f23487i = 1;

    /* renamed from: j, reason: collision with root package name */
    private static final int f23488j = 2;

    /* renamed from: k, reason: collision with root package name */
    private static final int f23489k = 3;

    /* renamed from: l, reason: collision with root package name */
    private static final int f23490l = 4;

    /* renamed from: m, reason: collision with root package name */
    private static final int f23491m = 5;

    /* renamed from: n, reason: collision with root package name */
    private static final int f23492n = 6;

    /* renamed from: o, reason: collision with root package name */
    private static final int f23493o = 7;

    /* renamed from: p, reason: collision with root package name */
    private static final int f23494p = 8;

    /* renamed from: q, reason: collision with root package name */
    private static final int f23495q = 9;

    /* renamed from: r, reason: collision with root package name */
    private static final int f23496r = 10;

    /* renamed from: s, reason: collision with root package name */
    private static final int f23497s = 22;

    /* renamed from: t, reason: collision with root package name */
    private static final int f23498t = 255;

    /* renamed from: a, reason: collision with root package name */
    private final int f23501a;

    /* renamed from: b, reason: collision with root package name */
    @k0
    private final List<ParcelUuid> f23502b;

    /* renamed from: c, reason: collision with root package name */
    private final SparseArray<byte[]> f23503c;

    /* renamed from: d, reason: collision with root package name */
    private final Map<ParcelUuid, byte[]> f23504d;

    /* renamed from: e, reason: collision with root package name */
    private final int f23505e;

    /* renamed from: f, reason: collision with root package name */
    private final String f23506f;

    /* renamed from: g, reason: collision with root package name */
    private final byte[] f23507g;
    

    /* renamed from: h, reason: collision with root package name */
    private static String f23486h = "ScanRecordUtil";

    /* renamed from: u, reason: collision with root package name */
    static final char[] f23499u = "0123456789ABCDEF".toCharArray();

    /* renamed from: v, reason: collision with root package name */
    public static final ParcelUuid f23500v = ParcelUuid.fromString("00000000-0000-1000-8000-00805F9B34FB");

    

    private g(List<ParcelUuid> list, SparseArray<byte[]> sparseArray, Map<ParcelUuid, byte[]> map, int i5, int i6, String str, byte[] bArr) {
        this.f23502b = list;
        this.f23503c = sparseArray;
        this.f23504d = map;
        this.f23506f = str;
        this.f23501a = i5;
        this.f23505e = i6;
        this.f23507g = bArr;
    }

    public static String a(byte[] bArr) {
        char[] cArr = new char[bArr.length * 2];
        for (int i5 = 0; i5 < bArr.length; i5++) {
            int i6 = bArr[i5] & 255;
            int i7 = i5 * 2;
            char[] cArr2 = f23499u;
            cArr[i7] = cArr2[i6 >>> 4];
            cArr[i7 + 1] = cArr2[i6 & 15];
        }
        return new String(cArr);
    }

    private static byte[] b(byte[] bArr, int i5, int i6) {
        byte[] bArr2 = new byte[i6];
        System.arraycopy((Object) bArr, i5, (Object) bArr2, 0, i6);
        return bArr2;
    }

    /* JADX WARN: Removed duplicated region for block: B:38:0x00ad  */
    /* JADX WARN: Removed duplicated region for block: B:42:0x00af  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public static g l(byte[] bArr) {
        if (bArr == null) {
            return null;
        }
        Log.e("ScanRecordUtilMYX23P", "进入parseFromBytes");
        ArrayList arrayList = new ArrayList();
        SparseArray sparseArray = new SparseArray();
        ArrayMap arrayMap = new ArrayMap();
        int i5 = 0;
        String str = null;
        byte b6 = -2147483648;
        int i6 = -1;
        while (i5 < bArr.length) {
            try {
                int i7 = i5 + 1;
                int i8 = bArr[i5] & 255;
                if (i8 == 0) {
                    return new g(!arrayList.isEmpty() ? null : arrayList, sparseArray, arrayMap, i6, b6, str, bArr);
                }
                int i9 = i8 - 1;
                int i10 = i7 + 1;
                int i11 = bArr[i7] & 255;
                if (i11 == 22) {
                    arrayMap.put(n(b(bArr, i10, 16)), b(bArr, i10 + 16, i9 - 16));
                } else if (i11 != 255) {
                    switch (i11) {
                        case 1:
                            i6 = bArr[i10] & 255;
                            break;
                        case 2:
                        case 3:
                            m(bArr, i10, i9, 16, arrayList);
                            break;
                        case 4:
                        case 5:
                            m(bArr, i10, i9, 32, arrayList);
                            break;
                        case 6:
                        case 7:
                            m(bArr, i10, i9, 128, arrayList);
                            break;
                        case 8:
                        case 9:
                            str = new String(b(bArr, i10, i9));
                            break;
                        case 10:
                            b6 = bArr[i10];
                            break;
                    }
                } else {
                    sparseArray.put(((bArr[i10 + 1] & 255) << 8) + (255 & bArr[i10]), b(bArr, i10 + 2, i9 - 2));
                }
                i5 = i9 + i10;
            } catch (Exception unused) {
                Log.e("ScanRecordUtil", "unable to parse scan record: " + Arrays.toString(bArr));
                return new g(null, null, null, -1, Integer.MIN_VALUE, null, bArr);
            }
        }
        return new g(!arrayList.isEmpty() ? null : arrayList, sparseArray, arrayMap, i6, b6, str, bArr);
    }

    private static int m(byte[] bArr, int i5, int i6, int i7, List<ParcelUuid> list) {
        int i8 = i5;
        int i9 = i6;
        while (i9 > 0) {
            list.add(n(b(bArr, i8, i7)));
            i9 -= i7;
            i8 += i7;
        }
        return i8;
    }

    public static ParcelUuid n(byte[] bArr) {
        if (bArr == null) {
            throw new IllegalArgumentException("uuidBytes cannot be null");
        }
        int length = bArr.length;
        if (length != 16 && length != 32 && length != 128) {
            throw new IllegalArgumentException("uuidBytes length invalid - " + length);
        }
        if (length == 128) {
            ByteBuffer order = ByteBuffer.wrap(bArr).order(ByteOrder.LITTLE_ENDIAN);
            return new ParcelUuid(new UUID(order.getLong(8), order.getLong(0)));
        }
        long j5 = length == 16 ? (bArr[0] & 255) + ((bArr[1] & 255) << 8) : (bArr[0] & 255) + ((bArr[1] & 255) << 8) + ((bArr[2] & 255) << 16) + ((bArr[3] & 255) << 24);
        ParcelUuid parcelUuid = f23500v;
        return new ParcelUuid(new UUID(parcelUuid.getUuid().getMostSignificantBits() + (j5 << 32), parcelUuid.getUuid().getLeastSignificantBits()));
    }

    static String o(SparseArray<byte[]> sparseArray) {
        if (sparseArray == null) {
            return "null";
        }
        if (sparseArray.size() == 0) {
            return "{}";
        }
        StringBuilder sb = new StringBuilder();
        sb.append('{');
        for (int i5 = 0; i5 < sparseArray.size(); i5++) {
            sb.append(sparseArray.keyAt(i5));
            sb.append("=");
            sb.append(Arrays.toString(sparseArray.valueAt(i5)));
        }
        sb.append('}');
        return sb.toString();
    }

    static <T> String p(Map<T, byte[]> map) {
        if (map == null) {
            return "null";
        }
        if (map.isEmpty()) {
            return "{}";
        }
        StringBuilder sb = new StringBuilder();
        sb.append('{');
        Iterator<Map.Entry<T, byte[]>> iterator2 = map.entrySet().iterator2();
        while (iterator2.hasNext()) {
            T key = iterator2.next().getKey();
            sb.append((Object) key);
            sb.append("=");
            sb.append(Arrays.toString(map.get(key)));
            if (iterator2.hasNext()) {
                sb.append(", ");
            }
        }
        sb.append('}');
        return sb.toString();
    }

    public int c() {
        return this.f23501a;
    }

    public byte[] d() {
        return this.f23507g;
    }

    @k0
    public String e() {
        return this.f23506f;
    }

    public SparseArray<byte[]> f() {
        return this.f23503c;
    }

    @k0
    public byte[] g(int i5) {
        return this.f23503c.get(i5);
    }

    public Map<ParcelUuid, byte[]> h() {
        return this.f23504d;
    }

    @k0
    public byte[] i(ParcelUuid parcelUuid) {
        if (parcelUuid == null) {
            return null;
        }
        return this.f23504d.get(parcelUuid);
    }

    public List<ParcelUuid> j() {
        return this.f23502b;
    }

    public int k() {
        return this.f23505e;
    }

    public String toString() {
        return "ScanRecord [mAdvertiseFlags=" + this.f23501a + ", mServiceUuids=" + ((Object) this.f23502b) + ", mManufacturerSpecificData=" + o(this.f23503c) + ", mServiceDa" + p(this.f23504d) + "௨௽஡, mTxPowerLevel=" + this.f23505e + ", mDevice" + this.f23506f + "㪒㪽㪱㪹㫡]";
    }
}
