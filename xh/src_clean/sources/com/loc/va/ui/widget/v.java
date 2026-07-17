package com.loc.va.ui.widget;

import android.content.Context;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Rect;
import android.view.View;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import com.loc.va.c;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class v extends RecyclerView.n {

    /* renamed from: a, reason: collision with root package name */
    private int f23464a;

    /* renamed from: b, reason: collision with root package name */
    private int f23465b;

    /* renamed from: c, reason: collision with root package name */
    private Paint f23466c;

    /* renamed from: d, reason: collision with root package name */
    private Paint f23467d;

    /* renamed from: e, reason: collision with root package name */
    private Paint f23468e;

    /* renamed from: f, reason: collision with root package name */
    private Rect f23469f = new Rect();

    public v(Context context) {
        this.f23464a = d(context, 40.0f);
        this.f23465b = d(context, 6.0f);
        Paint paint = new Paint(1);
        this.f23467d = paint;
        paint.setColor(context.getResources().getColor(c.f.G1));
        Paint paint2 = new Paint(1);
        this.f23466c = paint2;
        paint2.setTextSize(48.0f);
        this.f23466c.setColor(context.getResources().getColor(2131099689));
        Paint paint3 = new Paint(1);
        this.f23468e = paint3;
        paint3.setColor(-7829368);
    }

    private int d(Context context, float f5) {
        return (int) ((f5 * context.getResources().getDisplayMetrics().density) + 0.5f);
    }

    @Override // androidx.recyclerview.widget.RecyclerView.n
    public void getItemOffsets(Rect rect, View view, RecyclerView recyclerView, RecyclerView.b0 b0Var) {
        if (recyclerView.getAdapter() instanceof com.loc.va.ui.adapters.k) {
            rect.top = ((com.loc.va.ui.adapters.k) recyclerView.getAdapter()).q(recyclerView.getChildLayoutPosition(view)) ? this.f23464a : 1;
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView.n
    public void onDraw(Canvas canvas, RecyclerView recyclerView, RecyclerView.b0 b0Var) {
        if (recyclerView.getAdapter() instanceof com.loc.va.ui.adapters.k) {
            com.loc.va.ui.adapters.k kVar = (com.loc.va.ui.adapters.k) recyclerView.getAdapter();
            int childCount = recyclerView.getChildCount();
            for (int i5 = 0; i5 < childCount; i5++) {
                View childAt = recyclerView.getChildAt(i5);
                int childLayoutPosition = recyclerView.getChildLayoutPosition(childAt);
                boolean q5 = kVar.q(childLayoutPosition);
                int paddingLeft = recyclerView.getPaddingLeft();
                int width = recyclerView.getWidth() - recyclerView.getPaddingRight();
                if (q5) {
                    canvas.drawRect(paddingLeft, childAt.getTop() - this.f23464a, width, childAt.getTop(), this.f23467d);
                    this.f23466c.getTextBounds(kVar.p(childLayoutPosition), 0, kVar.p(childLayoutPosition).length(), this.f23469f);
                    String p5 = kVar.p(childLayoutPosition);
                    float f5 = paddingLeft + this.f23465b;
                    int top2 = childAt.getTop();
                    int i6 = this.f23464a;
                    canvas.drawText(p5, f5, (top2 - i6) + (i6 / 2) + (this.f23469f.height() / 2), this.f23466c);
                } else {
                    canvas.drawRect(paddingLeft, childAt.getTop() - 1, width, childAt.getTop(), this.f23468e);
                }
            }
        }
    }

    @Override // androidx.recyclerview.widget.RecyclerView.n
    public void onDrawOver(Canvas canvas, RecyclerView recyclerView, RecyclerView.b0 b0Var) {
        String p5;
        float f5;
        int height;
        if (recyclerView.getAdapter() instanceof com.loc.va.ui.adapters.k) {
            com.loc.va.ui.adapters.k kVar = (com.loc.va.ui.adapters.k) recyclerView.getAdapter();
            int findFirstVisibleItemPosition = ((LinearLayoutManager) recyclerView.getLayoutManager()).findFirstVisibleItemPosition();
            View view = recyclerView.findViewHolderForAdapterPosition(findFirstVisibleItemPosition).itemView;
            boolean q5 = kVar.q(findFirstVisibleItemPosition + 1);
            int paddingTop = recyclerView.getPaddingTop();
            int paddingLeft = recyclerView.getPaddingLeft();
            int width = recyclerView.getWidth() - recyclerView.getPaddingRight();
            if (q5) {
                int min = Math.min(this.f23464a, view.getBottom());
                canvas.drawRect(paddingLeft, (view.getTop() + paddingTop) - this.f23464a, width, paddingTop + min, this.f23467d);
                this.f23466c.getTextBounds(kVar.p(findFirstVisibleItemPosition), 0, kVar.p(findFirstVisibleItemPosition).length(), this.f23469f);
                p5 = kVar.p(findFirstVisibleItemPosition);
                f5 = paddingLeft + this.f23465b;
                height = ((paddingTop + (this.f23464a / 2)) + (this.f23469f.height() / 2)) - (this.f23464a - min);
            } else {
                canvas.drawRect(paddingLeft, paddingTop, width, this.f23464a + paddingTop, this.f23467d);
                this.f23466c.getTextBounds(kVar.p(findFirstVisibleItemPosition), 0, kVar.p(findFirstVisibleItemPosition).length(), this.f23469f);
                p5 = kVar.p(findFirstVisibleItemPosition);
                f5 = paddingLeft + this.f23465b;
                height = paddingTop + (this.f23464a / 2) + (this.f23469f.height() / 2);
            }
            canvas.drawText(p5, f5, height, this.f23466c);
            canvas.save();
        }
    }
}
