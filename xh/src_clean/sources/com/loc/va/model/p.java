package com.loc.va.model;

import com.baidu.mapapi.model.LatLng;
import java.io.Serializable;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class p implements Serializable {
    private String address;
    private LatLng bdLatLng;
    private String city;
    private int cityCode;
    private String country;
    private String district;
    private m gcj02LatLng;
    private String province;
    private String simpleAddress;
    private String street;
    private String streetNumber;
    private String town;

    public String getAddress() {
        return this.address;
    }

    public LatLng getBdLatLng() {
        return this.bdLatLng;
    }

    public String getCity() {
        return this.city;
    }

    public int getCityCode() {
        return this.cityCode;
    }

    public String getCountry() {
        return this.country;
    }

    public String getDistrict() {
        return this.district;
    }

    public m getGcj02LatLng() {
        return this.gcj02LatLng;
    }

    public String getProvince() {
        return this.province;
    }

    public String getSimpleAddress() {
        return this.simpleAddress;
    }

    public String getStreet() {
        return this.street;
    }

    public String getStreetNumber() {
        return this.streetNumber;
    }

    public String getTown() {
        return this.town;
    }

    public void setAddress(String str) {
        this.address = str;
    }

    public void setBdLatLng(LatLng latLng) {
        this.bdLatLng = latLng;
    }

    public void setCity(String str) {
        this.city = str;
    }

    public void setCityCode(int i5) {
        this.cityCode = i5;
    }

    public void setCountry(String str) {
        this.country = str;
    }

    public void setDistrict(String str) {
        this.district = str;
    }

    public void setGcj02LatLng(m mVar) {
        this.gcj02LatLng = mVar;
    }

    public void setProvince(String str) {
        this.province = str;
    }

    public void setSimpleAddress(String str) {
        this.simpleAddress = str;
    }

    public void setStreet(String str) {
        this.street = str;
    }

    public void setStreetNumber(String str) {
        this.streetNumber = str;
    }

    public void setTown(String str) {
        this.town = str;
    }
}
