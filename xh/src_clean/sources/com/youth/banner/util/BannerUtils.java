package com.youth.banner.util;

import android.content.res.Resources;
import android.graphics.Outline;
import android.util.TypedValue;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.view.ViewOutlineProvider;
import b.e0;
import b.j0;
import b.o0;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class BannerUtils {
    public static float dp2px(float f5) {
        return TypedValue.applyDimension(1, f5, Resources.getSystem().getDisplayMetrics());
    }

    public static int getRealPosition(boolean z5, int i5, int i6) {
        if (!z5) {
            return i5;
        }
        if (i5 == 0) {
            return i6 - 1;
        }
        if (i5 == i6 + 1) {
            return 0;
        }
        return i5 - 1;
    }

    public static View getView(@j0 ViewGroup viewGroup, @e0 int i5) {
        View inflate = LayoutInflater.from(viewGroup.getContext()).inflate(i5, viewGroup, false);
        ViewGroup.LayoutParams layoutParams = inflate.getLayoutParams();
        if (layoutParams.height != -1 || layoutParams.width != -1) {
            layoutParams.height = -1;
            layoutParams.width = -1;
            inflate.setLayoutParams(layoutParams);
        }
        return inflate;
    }

    @o0(api = 21)
    public static void setBannerRound(View view, final float f5) {
        view.setOutlineProvider(new ViewOutlineProvider() { // from class: com.youth.banner.util.BannerUtils.1
            @Override // android.view.ViewOutlineProvider
            public void getOutline(View view2, Outline outline) {
                outline.setRoundRect(0, 0, view2.getWidth(), view2.getHeight(), f5);
            }
        });
        view.setClipToOutline(true);
    }
}
