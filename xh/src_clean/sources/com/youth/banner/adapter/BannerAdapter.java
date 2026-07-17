package com.youth.banner.adapter;

import android.view.View;
import android.view.ViewGroup;
import androidx.recyclerview.widget.RecyclerView;
import androidx.recyclerview.widget.RecyclerView.e0;
import b.j0;
import com.youth.banner.holder.IViewHolder;
import com.youth.banner.listener.OnBannerListener;
import com.youth.banner.util.BannerUtils;
import java.util.ArrayList;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public abstract class BannerAdapter<T, VH extends RecyclerView.e0> extends RecyclerView.g<VH> implements IViewHolder<T, VH> {
    private OnBannerListener mOnBannerListener;
    private VH mViewHolder;
    protected List<T> mDatas = new ArrayList();
    private int increaseCount = 2;

    public BannerAdapter(List<T> list) {
        setDatas(list);
    }

    /* JADX INFO: Access modifiers changed from: private */
    public /* synthetic */ void lambda$onBindViewHolder$0(int i5, View view) {
        this.mOnBannerListener.OnBannerClick(this.mDatas.get(i5), i5);
    }

    public T getData(int i5) {
        return this.mDatas.get(i5);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public int getItemCount() {
        return getRealCount() > 1 ? getRealCount() + this.increaseCount : getRealCount();
    }

    public int getRealCount() {
        List<T> list = this.mDatas;
        if (list == null) {
            return 0;
        }
        return list.size();
    }

    public int getRealPosition(int i5) {
        return BannerUtils.getRealPosition(this.increaseCount == 2, i5, getRealCount());
    }

    public VH getViewHolder() {
        return this.mViewHolder;
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    public final void onBindViewHolder(@j0 VH vh, int i5) {
        this.mViewHolder = vh;
        final int realPosition = getRealPosition(i5);
        onBindView(vh, this.mDatas.get(realPosition), realPosition, getRealCount());
        if (this.mOnBannerListener != null) {
            vh.itemView.setOnClickListener(new View.OnClickListener() { // from class: com.youth.banner.adapter.a
                @Override // android.view.View.OnClickListener
                public final void onClick(View view) {
                    BannerAdapter.this.lambda$onBindViewHolder$0(realPosition, view);
                }
            });
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView.g
    @j0
    public VH onCreateViewHolder(@j0 ViewGroup viewGroup, int i5) {
        return (VH) onCreateHolder(viewGroup, i5);
    }

    public void setDatas(List<T> list) {
        if (list == null) {
            list = new ArrayList<>();
        }
        this.mDatas = list;
    }

    public void setIncreaseCount(int i5) {
        this.increaseCount = i5;
    }

    public void setOnBannerListener(OnBannerListener onBannerListener) {
        this.mOnBannerListener = onBannerListener;
    }
}
