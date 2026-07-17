package com.youth.banner.itemdecoration;

import android.graphics.Rect;
import android.view.View;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import b.j0;
import b.m0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes08.dex */
public class MarginDecoration extends RecyclerView.n {
    
    private int mMarginPx;

    

    public MarginDecoration(@m0 int i5) {
        this.mMarginPx = i5;
    }

    private LinearLayoutManager requireLinearLayoutManager(@j0 RecyclerView recyclerView) {
        RecyclerView.o layoutManager = recyclerView.getLayoutManager();
        if (layoutManager instanceof LinearLayoutManager) {
            return (LinearLayoutManager) layoutManager;
        }
        throw new IllegalStateException("The layoutManager must be LinearLayoutManager");
    }

    @Override // androidx.recyclerview.widget.RecyclerView.n
    public void getItemOffsets(@j0 Rect rect, @j0 View view, @j0 RecyclerView recyclerView, @j0 RecyclerView.b0 b0Var) {
        if (requireLinearLayoutManager(recyclerView).getOrientation() == 1) {
            int i5 = this.mMarginPx;
            rect.top = i5;
            rect.bottom = i5;
        } else {
            int i6 = this.mMarginPx;
            rect.left = i6;
            rect.right = i6;
        }
    }
}
