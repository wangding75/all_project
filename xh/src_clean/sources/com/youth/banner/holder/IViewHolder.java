package com.youth.banner.holder;

import android.view.ViewGroup;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public interface IViewHolder<T, VH> {
    void onBindView(VH vh, T t5, int i5, int i6);

    VH onCreateHolder(ViewGroup viewGroup, int i5);
}
