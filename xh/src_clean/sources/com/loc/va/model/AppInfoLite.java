package com.loc.va.model;

import android.net.Uri;
import android.os.Parcel;
import android.os.Parcelable;
import java.io.File;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class AppInfoLite implements Parcelable {
    
    public static final Parcelable.Creator<AppInfoLite> CREATOR = new a();

    /* renamed from: a, reason: collision with root package name */
    public String f22627a;

    /* renamed from: b, reason: collision with root package name */
    public String f22628b;

    /* renamed from: c, reason: collision with root package name */
    public String f22629c;

    /* renamed from: d, reason: collision with root package name */
    public boolean f22630d;

    /* renamed from: e, reason: collision with root package name */
    public int f22631e;

    /* renamed from: f, reason: collision with root package name */
    public String[] f22632f;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    class a implements Parcelable.Creator<AppInfoLite> {
        a() {
        }

        @Override // android.os.Parcelable.Creator
        /* renamed from: a, reason: merged with bridge method [inline-methods] */
        public AppInfoLite createFromParcel(Parcel parcel) {
            return new AppInfoLite(parcel);
        }

        @Override // android.os.Parcelable.Creator
        /* renamed from: b, reason: merged with bridge method [inline-methods] */
        public AppInfoLite[] newArray(int i5) {
            return new AppInfoLite[i5];
        }
    }

    

    protected AppInfoLite(Parcel parcel) {
        this.f22627a = parcel.readString();
        this.f22628b = parcel.readString();
        this.f22629c = parcel.readString();
        this.f22630d = parcel.readByte() != 0;
        this.f22631e = parcel.readInt();
        this.f22632f = parcel.createStringArray();
    }

    public AppInfoLite(c cVar) {
        this(cVar.f22635a, cVar.f22636b, String.valueOf(cVar.f22639e), cVar.f22637c, cVar.f22641g, cVar.f22642h);
    }

    public AppInfoLite(String str, String str2, String str3, boolean z5, int i5, String[] strArr) {
        this.f22627a = str;
        this.f22628b = str2;
        this.f22629c = str3;
        this.f22630d = z5;
        this.f22631e = i5;
        this.f22632f = strArr;
    }

    public AppInfoLite(String str, String str2, String str3, boolean z5, String[] strArr) {
        this.f22627a = str;
        this.f22628b = str2;
        this.f22629c = str3;
        this.f22630d = z5;
        this.f22632f = strArr;
    }

    public Uri c() {
        if (!this.f22630d) {
            return Uri.fromFile(new File(this.f22628b));
        }
        return Uri.parse("package:" + this.f22627a);
    }

    @Override // android.os.Parcelable
    public int describeContents() {
        return 0;
    }

    @Override // android.os.Parcelable
    public void writeToParcel(Parcel parcel, int i5) {
        parcel.writeString(this.f22627a);
        parcel.writeString(this.f22628b);
        parcel.writeString(this.f22629c);
        parcel.writeByte(this.f22630d ? (byte) 1 : (byte) 0);
        parcel.writeInt(this.f22631e);
        parcel.writeStringArray(this.f22632f);
    }
}
