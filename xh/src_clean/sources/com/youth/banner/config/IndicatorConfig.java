package com.youth.banner.config;

import b.l;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class IndicatorConfig {
    private int currentPosition;
    private int indicatorSize;
    private Margins margins;
    private int gravity = 1;
    private int indicatorSpace = BannerConfig.INDICATOR_SPACE;
    private int normalWidth = BannerConfig.INDICATOR_NORMAL_WIDTH;
    private int selectedWidth = BannerConfig.INDICATOR_SELECTED_WIDTH;

    @l
    private int normalColor = BannerConfig.INDICATOR_NORMAL_COLOR;

    @l
    private int selectedColor = BannerConfig.INDICATOR_SELECTED_COLOR;
    private int radius = BannerConfig.INDICATOR_RADIUS;
    private int height = BannerConfig.INDICATOR_HEIGHT;
    private boolean attachToBanner = true;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    @Retention(RetentionPolicy.SOURCE)
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public @interface Direction {
        public static final int CENTER = 1;
        public static final int LEFT = 0;
        public static final int RIGHT = 2;
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    public static class Margins {
        public int bottomMargin;
        public int leftMargin;
        public int rightMargin;
        public int topMargin;

        public Margins() {
            this(BannerConfig.INDICATOR_MARGIN);
        }

        public Margins(int i5) {
            this(i5, i5, i5, i5);
        }

        public Margins(int i5, int i6, int i7, int i8) {
            this.leftMargin = i5;
            this.topMargin = i6;
            this.rightMargin = i7;
            this.bottomMargin = i8;
        }
    }

    public int getCurrentPosition() {
        return this.currentPosition;
    }

    public int getGravity() {
        return this.gravity;
    }

    public int getHeight() {
        return this.height;
    }

    public int getIndicatorSize() {
        return this.indicatorSize;
    }

    public int getIndicatorSpace() {
        return this.indicatorSpace;
    }

    public Margins getMargins() {
        if (this.margins == null) {
            setMargins(new Margins());
        }
        return this.margins;
    }

    public int getNormalColor() {
        return this.normalColor;
    }

    public int getNormalWidth() {
        return this.normalWidth;
    }

    public int getRadius() {
        return this.radius;
    }

    public int getSelectedColor() {
        return this.selectedColor;
    }

    public int getSelectedWidth() {
        return this.selectedWidth;
    }

    public boolean isAttachToBanner() {
        return this.attachToBanner;
    }

    public IndicatorConfig setAttachToBanner(boolean z5) {
        this.attachToBanner = z5;
        return this;
    }

    public IndicatorConfig setCurrentPosition(int i5) {
        this.currentPosition = i5;
        return this;
    }

    public IndicatorConfig setGravity(int i5) {
        this.gravity = i5;
        return this;
    }

    public IndicatorConfig setHeight(int i5) {
        this.height = i5;
        return this;
    }

    public IndicatorConfig setIndicatorSize(int i5) {
        this.indicatorSize = i5;
        return this;
    }

    public IndicatorConfig setIndicatorSpace(int i5) {
        this.indicatorSpace = i5;
        return this;
    }

    public IndicatorConfig setMargins(Margins margins) {
        this.margins = margins;
        return this;
    }

    public IndicatorConfig setNormalColor(int i5) {
        this.normalColor = i5;
        return this;
    }

    public IndicatorConfig setNormalWidth(int i5) {
        this.normalWidth = i5;
        return this;
    }

    public IndicatorConfig setRadius(int i5) {
        this.radius = i5;
        return this;
    }

    public IndicatorConfig setSelectedColor(int i5) {
        this.selectedColor = i5;
        return this;
    }

    public IndicatorConfig setSelectedWidth(int i5) {
        this.selectedWidth = i5;
        return this;
    }
}
