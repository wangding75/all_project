package com.loc.va.ui.adapters;

import android.os.Build;
import android.os.Environment;
import android.os.storage.StorageManager;
import android.os.storage.StorageVolume;
import androidx.fragment.app.Fragment;
import androidx.fragment.app.FragmentManager;
import com.loc.va.App;
import com.loc.va.c;
import java.io.File;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class c extends androidx.fragment.app.p {
    

    /* renamed from: n, reason: collision with root package name */
    private List<String> f22985n;

    /* renamed from: o, reason: collision with root package name */
    private List<File> f22986o;

    

    public c(FragmentManager fragmentManager) {
        super(fragmentManager);
        List<StorageVolume> storageVolumes;
        this.f22985n = new ArrayList();
        this.f22986o = new ArrayList();
        this.f22985n.add(App.a().getResources().getString(c.p.f22150z0));
        this.f22986o.add(null);
        if (Build.VERSION.SDK_INT < 24) {
            File externalStorageDirectory = Environment.getExternalStorageDirectory();
            if (externalStorageDirectory == null || !externalStorageDirectory.isDirectory()) {
                return;
            }
            this.f22985n.add(App.a().getResources().getString(c.p.f22043h1));
            this.f22986o.add(externalStorageDirectory);
            return;
        }
        storageVolumes = ((StorageManager) App.a().getSystemService("storage")).getStorageVolumes();
        for (StorageVolume storageVolume : storageVolumes) {
            File file = (File) com.lody.virtual.helper.utils.p.y(storageVolume).e("getPathFile").q();
            String str = (String) com.lody.virtual.helper.utils.p.y(storageVolume).e("getUserLabel").q();
            if (file.listFiles() != null) {
                this.f22985n.add(str);
                this.f22986o.add(file);
            }
        }
    }

    @Override // androidx.viewpager.widget.a
    public int e() {
        return this.f22985n.size();
    }

    @Override // androidx.viewpager.widget.a
    public CharSequence g(int i5) {
        return this.f22985n.get(i5);
    }

    @Override // androidx.fragment.app.p
    public Fragment v(int i5) {
        return com.loc.va.home.t.r(this.f22986o.get(i5));
    }
}
