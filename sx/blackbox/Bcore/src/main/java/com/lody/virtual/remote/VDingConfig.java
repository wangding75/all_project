package com.lody.virtual.remote;

import android.os.Parcel;
import android.os.Parcelable;
import java.util.ArrayList;
import java.util.List;

/**
 * Stub implementation of VDingConfig for DingTalk compatibility.
 */
public class VDingConfig implements Parcelable {
    public static final int f24769p = 6;

    public String a;
    public String b;
    public String c;
    public String d;
    public List<String> e = new ArrayList<>();
    public boolean f = true; // Force enabled
    public String g;
    public String h;
    public String i;
    public String j;
    public String k;
    public String l;
    public String m;
    public int n = 1; // Default mode
    public int o = 0;

    public static final Parcelable.Creator<VDingConfig> CREATOR = new Parcelable.Creator<VDingConfig>() {
        @Override
        public VDingConfig createFromParcel(Parcel parcel) {
            return new VDingConfig(parcel);
        }

        @Override
        public VDingConfig[] newArray(int size) {
            return new VDingConfig[size];
        }
    };

    public VDingConfig() {
        this.f = true;
        this.n = 1;
    }

    protected VDingConfig(Parcel parcel) {
        this.a = parcel.readString();
        this.b = parcel.readString();
        this.c = parcel.readString();
        this.d = parcel.readString();
        parcel.readStringList(this.e);
        this.f = parcel.readByte() != 0;
        this.g = parcel.readString();
        this.h = parcel.readString();
        this.i = parcel.readString();
        this.j = parcel.readString();
        this.k = parcel.readString();
        this.l = parcel.readString();
        this.m = parcel.readString();
        this.n = parcel.readInt();
        this.o = parcel.readInt();
    }

    @Override
    public int describeContents() {
        return 0;
    }

    @Override
    public void writeToParcel(Parcel parcel, int flags) {
        parcel.writeString(this.a);
        parcel.writeString(this.b);
        parcel.writeString(this.c);
        parcel.writeString(this.d);
        parcel.writeStringList(this.e);
        parcel.writeByte((byte) (this.f ? 1 : 0));
        parcel.writeString(this.g);
        parcel.writeString(this.h);
        parcel.writeString(this.i);
        parcel.writeString(this.j);
        parcel.writeString(this.k);
        parcel.writeString(this.l);
        parcel.writeString(this.m);
        parcel.writeInt(this.n);
        parcel.writeInt(this.o);
    }
}
