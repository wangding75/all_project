package com.youth.banner.adapter;

import android.view.ViewGroup;
import android.widget.ImageView;
import com.youth.banner.holder.BannerImageHolder;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public abstract class BannerImageAdapter<T> extends BannerAdapter<T, BannerImageHolder> {
    public BannerImageAdapter(List<T> list) {
        super(list);
    }

    @Override // com.youth.banner.holder.IViewHolder
    public BannerImageHolder onCreateHolder(ViewGroup viewGroup, int i5) {
        ImageView imageView = new ImageView(viewGroup.getContext());
        imageView.setLayoutParams(new ViewGroup.LayoutParams(-1, -1));
        imageView.setScaleType(ImageView.ScaleType.CENTER_CROP);
        return new BannerImageHolder(imageView);
    }
}
