package com.youth.banner;

import android.content.Context;
import android.content.res.TypedArray;
import android.graphics.Canvas;
import android.graphics.Paint;
import android.graphics.Path;
import android.graphics.PorterDuff;
import android.graphics.PorterDuffXfermode;
import android.graphics.RectF;
import android.util.AttributeSet;
import android.view.MotionEvent;
import android.view.ViewConfiguration;
import android.view.ViewParent;
import android.widget.FrameLayout;
import androidx.core.content.h;
import androidx.lifecycle.p;
import androidx.recyclerview.widget.RecyclerView;
import androidx.viewpager2.widget.CompositePageTransformer;
import androidx.viewpager2.widget.MarginPageTransformer;
import androidx.viewpager2.widget.ViewPager2;
import b.k0;
import b.l;
import b.n;
import b.o0;
import com.youth.banner.adapter.BannerAdapter;
import com.youth.banner.config.BannerConfig;
import com.youth.banner.config.IndicatorConfig;
import com.youth.banner.indicator.Indicator;
import com.youth.banner.listener.OnBannerListener;
import com.youth.banner.listener.OnPageChangeListener;
import com.youth.banner.transformer.MZScaleInTransformer;
import com.youth.banner.transformer.ScaleInTransformer;
import com.youth.banner.util.BannerLifecycleObserver;
import com.youth.banner.util.BannerLifecycleObserverAdapter;
import com.youth.banner.util.BannerUtils;
import com.youth.banner.util.LogUtils;
import com.youth.banner.util.ScrollSpeedManger;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.ref.WeakReference;
import java.util.List;

/* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
/* loaded from: D:\github\xh\blackdex_out\classes10.dex */
public class Banner<T, BA extends BannerAdapter> extends FrameLayout implements BannerLifecycleObserver {
    public static final int HORIZONTAL = 0;
    public static final int INVALID_VALUE = -1;
    public static final int VERTICAL = 1;
    private int indicatorGravity;
    private int indicatorHeight;
    private int indicatorMargin;
    private int indicatorMarginBottom;
    private int indicatorMarginLeft;
    private int indicatorMarginRight;
    private int indicatorMarginTop;
    private int indicatorRadius;
    private int indicatorSpace;
    private boolean isIntercept;
    private BA mAdapter;
    private RecyclerView.i mAdapterDataObserver;
    private float mBannerRadius;
    private CompositePageTransformer mCompositePageTransformer;
    private Paint mImagePaint;
    private Indicator mIndicator;
    private boolean mIsAutoLoop;
    private boolean mIsInfiniteLoop;
    private boolean mIsViewPager2Drag;
    private AutoLoopTask mLoopTask;
    private long mLoopTime;
    private OnPageChangeListener mOnPageChangeListener;
    private Banner<T, BA>.BannerOnPageChangeCallback mPageChangeCallback;
    private Paint mRoundPaint;
    private int mScrollTime;
    private int mStartPosition;
    private float mStartX;
    private float mStartY;
    private int mTouchSlop;
    private ViewPager2 mViewPager2;
    private int normalColor;
    private int normalWidth;
    private int selectedColor;
    private int selectedWidth;

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    static class AutoLoopTask implements Runnable {
        private final WeakReference<Banner> reference;

        AutoLoopTask(Banner banner) {
            this.reference = new WeakReference<>(banner);
        }

        @Override // java.lang.Runnable
        public void run() {
            int itemCount;
            Banner banner = this.reference.get();
            if (banner == null || !banner.mIsAutoLoop || (itemCount = banner.getItemCount()) == 0) {
                return;
            }
            banner.setCurrentItem((banner.getCurrentItem() + 1) % itemCount);
            banner.postDelayed(banner.mLoopTask, banner.mLoopTime);
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes07.dex
 */
    /* loaded from: D:\github\xh\blackdex_out\classes08.dex */
    class BannerOnPageChangeCallback extends ViewPager2.OnPageChangeCallback {
        private boolean isScrolled;
        private int mTempPosition = -1;

        BannerOnPageChangeCallback() {
        }

        @Override // androidx.viewpager2.widget.ViewPager2.OnPageChangeCallback
        public void onPageScrollStateChanged(int i5) {
            if (i5 == 1 || i5 == 2) {
                this.isScrolled = true;
            } else if (i5 == 0) {
                this.isScrolled = false;
                if (this.mTempPosition != -1 && Banner.this.mIsInfiniteLoop) {
                    int i6 = this.mTempPosition;
                    if (i6 == 0) {
                        Banner banner = Banner.this;
                        banner.setCurrentItem(banner.getRealCount(), false);
                    } else if (i6 == Banner.this.getItemCount() - 1) {
                        Banner.this.setCurrentItem(1, false);
                    }
                }
            }
            if (Banner.this.mOnPageChangeListener != null) {
                Banner.this.mOnPageChangeListener.onPageScrollStateChanged(i5);
            }
            if (Banner.this.mIndicator != null) {
                Banner.this.mIndicator.onPageScrollStateChanged(i5);
            }
        }

        @Override // androidx.viewpager2.widget.ViewPager2.OnPageChangeCallback
        public void onPageScrolled(int i5, float f5, int i6) {
            int realPosition = BannerUtils.getRealPosition(Banner.this.isInfiniteLoop(), i5, Banner.this.getRealCount());
            if (Banner.this.mOnPageChangeListener != null) {
                Banner.this.mOnPageChangeListener.onPageScrolled(realPosition, f5, i6);
            }
            if (Banner.this.mIndicator != null) {
                Banner.this.mIndicator.onPageScrolled(realPosition, f5, i6);
            }
        }

        @Override // androidx.viewpager2.widget.ViewPager2.OnPageChangeCallback
        public void onPageSelected(int i5) {
            if (this.isScrolled) {
                this.mTempPosition = i5;
                int realPosition = BannerUtils.getRealPosition(Banner.this.isInfiniteLoop(), i5, Banner.this.getRealCount());
                if (Banner.this.mOnPageChangeListener != null) {
                    Banner.this.mOnPageChangeListener.onPageSelected(realPosition);
                }
                if (Banner.this.mIndicator != null) {
                    Banner.this.mIndicator.onPageSelected(realPosition);
                }
            }
        }
    }

    /* JADX WARN: Classes with same name are omitted:
  D:\github\xh\blackdex_out\classes09.dex
 */
    @Retention(RetentionPolicy.SOURCE)
    public @interface Orientation {
    }

    public Banner(Context context) {
        this(context, null);
    }

    public Banner(Context context, AttributeSet attributeSet) {
        this(context, attributeSet, 0);
    }

    public Banner(Context context, AttributeSet attributeSet, int i5) {
        super(context, attributeSet, i5);
        this.mIsInfiniteLoop = true;
        this.mIsAutoLoop = true;
        this.mLoopTime = 3000L;
        this.mScrollTime = 600;
        this.mStartPosition = 1;
        this.mBannerRadius = 0.0f;
        this.normalWidth = BannerConfig.INDICATOR_NORMAL_WIDTH;
        this.selectedWidth = BannerConfig.INDICATOR_SELECTED_WIDTH;
        this.normalColor = BannerConfig.INDICATOR_NORMAL_COLOR;
        this.selectedColor = BannerConfig.INDICATOR_SELECTED_COLOR;
        this.indicatorGravity = 1;
        this.indicatorHeight = BannerConfig.INDICATOR_HEIGHT;
        this.indicatorRadius = BannerConfig.INDICATOR_RADIUS;
        this.isIntercept = true;
        this.mAdapterDataObserver = new RecyclerView.i() { // from class: com.youth.banner.Banner.1
            @Override // androidx.recyclerview.widget.RecyclerView.i
            public void onChanged() {
                if (Banner.this.getItemCount() <= 1) {
                    Banner.this.stop();
                } else {
                    Banner.this.start();
                }
                Banner.this.setIndicatorPageChange();
            }
        };
        init(context);
        initTypedArray(context, attributeSet);
    }

    private void drawBottomLeft(Canvas canvas) {
        int height = getHeight();
        Path path = new Path();
        float f5 = height;
        path.moveTo(0.0f, f5 - this.mBannerRadius);
        path.lineTo(0.0f, f5);
        path.lineTo(this.mBannerRadius, f5);
        float f6 = this.mBannerRadius;
        path.arcTo(new RectF(0.0f, f5 - (f6 * 2.0f), f6 * 2.0f, f5), 90.0f, 90.0f);
        path.close();
        canvas.drawPath(path, this.mRoundPaint);
    }

    private void drawBottomRight(Canvas canvas) {
        int height = getHeight();
        int width = getWidth();
        Path path = new Path();
        float f5 = width;
        float f6 = height;
        path.moveTo(f5 - this.mBannerRadius, f6);
        path.lineTo(f5, f6);
        path.lineTo(f5, f6 - this.mBannerRadius);
        float f7 = this.mBannerRadius;
        path.arcTo(new RectF(f5 - (f7 * 2.0f), f6 - (f7 * 2.0f), f5, f6), 0.0f, 90.0f);
        path.close();
        canvas.drawPath(path, this.mRoundPaint);
    }

    private void drawTopLeft(Canvas canvas) {
        Path path = new Path();
        path.moveTo(0.0f, this.mBannerRadius);
        path.lineTo(0.0f, 0.0f);
        path.lineTo(this.mBannerRadius, 0.0f);
        float f5 = this.mBannerRadius;
        path.arcTo(new RectF(0.0f, 0.0f, f5 * 2.0f, f5 * 2.0f), -90.0f, -90.0f);
        path.close();
        canvas.drawPath(path, this.mRoundPaint);
    }

    private void drawTopRight(Canvas canvas) {
        int width = getWidth();
        Path path = new Path();
        float f5 = width;
        path.moveTo(f5 - this.mBannerRadius, 0.0f);
        path.lineTo(f5, 0.0f);
        path.lineTo(f5, this.mBannerRadius);
        float f6 = this.mBannerRadius;
        path.arcTo(new RectF(f5 - (f6 * 2.0f), 0.0f, f5, f6 * 2.0f), 0.0f, -90.0f);
        path.close();
        canvas.drawPath(path, this.mRoundPaint);
    }

    private void init(Context context) {
        this.mTouchSlop = ViewConfiguration.get(context).getScaledTouchSlop() / 2;
        this.mCompositePageTransformer = new CompositePageTransformer();
        this.mPageChangeCallback = new BannerOnPageChangeCallback();
        this.mLoopTask = new AutoLoopTask(this);
        ViewPager2 viewPager2 = new ViewPager2(context);
        this.mViewPager2 = viewPager2;
        viewPager2.setLayoutParams(new FrameLayout.LayoutParams(-1, -1));
        this.mViewPager2.setOffscreenPageLimit(1);
        this.mViewPager2.registerOnPageChangeCallback(this.mPageChangeCallback);
        this.mViewPager2.setPageTransformer(this.mCompositePageTransformer);
        ScrollSpeedManger.reflectLayoutManager(this);
        addView(this.mViewPager2);
        Paint paint = new Paint();
        this.mRoundPaint = paint;
        paint.setColor(-1);
        this.mRoundPaint.setAntiAlias(true);
        this.mRoundPaint.setStyle(Paint.Style.FILL);
        this.mRoundPaint.setXfermode(new PorterDuffXfermode(PorterDuff.Mode.DST_OUT));
        Paint paint2 = new Paint();
        this.mImagePaint = paint2;
        paint2.setXfermode(null);
    }

    private void initIndicator() {
        if (this.mIndicator == null || getAdapter() == null) {
            return;
        }
        if (this.mIndicator.getIndicatorConfig().isAttachToBanner()) {
            removeIndicator();
            addView(this.mIndicator.getIndicatorView());
        }
        initIndicatorAttr();
        setIndicatorPageChange();
    }

    /* JADX WARN: Removed duplicated region for block: B:10:0x0035  */
    /* JADX WARN: Removed duplicated region for block: B:13:0x003c  */
    /* JADX WARN: Removed duplicated region for block: B:16:0x0043  */
    /* JADX WARN: Removed duplicated region for block: B:19:0x004a  */
    /* JADX WARN: Removed duplicated region for block: B:22:0x0051  */
    /* JADX WARN: Removed duplicated region for block: B:7:0x002d  */
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    private void initIndicatorAttr() {
        IndicatorConfig.Margins margins;
        int i5;
        int i6;
        int i7;
        int i8;
        int i9;
        int i10;
        int i11 = this.indicatorMargin;
        if (i11 == 0) {
            int i12 = this.indicatorMarginLeft;
            if (i12 != 0 || this.indicatorMarginTop != 0 || this.indicatorMarginRight != 0 || this.indicatorMarginBottom != 0) {
                margins = new IndicatorConfig.Margins(i12, this.indicatorMarginTop, this.indicatorMarginRight, this.indicatorMarginBottom);
            }
            i5 = this.indicatorSpace;
            if (i5 > 0) {
                setIndicatorSpace(i5);
            }
            i6 = this.indicatorGravity;
            if (i6 != 1) {
                setIndicatorGravity(i6);
            }
            i7 = this.normalWidth;
            if (i7 > 0) {
                setIndicatorNormalWidth(i7);
            }
            i8 = this.selectedWidth;
            if (i8 > 0) {
                setIndicatorSelectedWidth(i8);
            }
            i9 = this.indicatorHeight;
            if (i9 > 0) {
                setIndicatorHeight(i9);
            }
            i10 = this.indicatorRadius;
            if (i10 > 0) {
                setIndicatorRadius(i10);
            }
            setIndicatorNormalColor(this.normalColor);
            setIndicatorSelectedColor(this.selectedColor);
        }
        margins = new IndicatorConfig.Margins(i11);
        setIndicatorMargins(margins);
        i5 = this.indicatorSpace;
        if (i5 > 0) {
        }
        i6 = this.indicatorGravity;
        if (i6 != 1) {
        }
        i7 = this.normalWidth;
        if (i7 > 0) {
        }
        i8 = this.selectedWidth;
        if (i8 > 0) {
        }
        i9 = this.indicatorHeight;
        if (i9 > 0) {
        }
        i10 = this.indicatorRadius;
        if (i10 > 0) {
        }
        setIndicatorNormalColor(this.normalColor);
        setIndicatorSelectedColor(this.selectedColor);
    }

    private void initTypedArray(Context context, AttributeSet attributeSet) {
        if (attributeSet == null) {
            return;
        }
        TypedArray obtainStyledAttributes = context.obtainStyledAttributes(attributeSet, R.styleable.Banner);
        this.mBannerRadius = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_radius, 0);
        this.mLoopTime = obtainStyledAttributes.getInt(R.styleable.Banner_banner_loop_time, 3000);
        this.mIsAutoLoop = obtainStyledAttributes.getBoolean(R.styleable.Banner_banner_auto_loop, true);
        this.mIsInfiniteLoop = obtainStyledAttributes.getBoolean(R.styleable.Banner_banner_infinite_loop, true);
        this.normalWidth = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_normal_width, BannerConfig.INDICATOR_NORMAL_WIDTH);
        this.selectedWidth = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_selected_width, BannerConfig.INDICATOR_SELECTED_WIDTH);
        this.normalColor = obtainStyledAttributes.getColor(R.styleable.Banner_banner_indicator_normal_color, BannerConfig.INDICATOR_NORMAL_COLOR);
        this.selectedColor = obtainStyledAttributes.getColor(R.styleable.Banner_banner_indicator_selected_color, BannerConfig.INDICATOR_SELECTED_COLOR);
        this.indicatorGravity = obtainStyledAttributes.getInt(R.styleable.Banner_banner_indicator_gravity, 1);
        this.indicatorSpace = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_space, 0);
        this.indicatorMargin = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_margin, 0);
        this.indicatorMarginLeft = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_marginLeft, 0);
        this.indicatorMarginTop = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_marginTop, 0);
        this.indicatorMarginRight = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_marginRight, 0);
        this.indicatorMarginBottom = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_marginBottom, 0);
        this.indicatorHeight = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_height, BannerConfig.INDICATOR_HEIGHT);
        this.indicatorRadius = obtainStyledAttributes.getDimensionPixelSize(R.styleable.Banner_banner_indicator_radius, BannerConfig.INDICATOR_RADIUS);
        setOrientation(obtainStyledAttributes.getInt(R.styleable.Banner_banner_orientation, 0));
        setInfiniteLoop();
        obtainStyledAttributes.recycle();
    }

    private void setInfiniteLoop() {
        if (!isInfiniteLoop()) {
            isAutoLoop(false);
        }
        setStartPosition(isInfiniteLoop() ? 1 : 0);
    }

    private void setRecyclerViewPadding(int i5) {
        setRecyclerViewPadding(i5, i5);
    }

    private void setRecyclerViewPadding(int i5, int i6) {
        RecyclerView recyclerView = (RecyclerView) getViewPager2().getChildAt(0);
        if (getViewPager2().getOrientation() == 1) {
            recyclerView.setPadding(0, i5, 0, i6);
        } else {
            recyclerView.setPadding(i5, 0, i6, 0);
        }
        recyclerView.setClipToPadding(false);
    }

    public Banner addBannerLifecycleObserver(p pVar) {
        if (pVar != null) {
            pVar.getLifecycle().a(new BannerLifecycleObserverAdapter(pVar, this));
        }
        return this;
    }

    public Banner addItemDecoration(RecyclerView.n nVar) {
        getViewPager2().addItemDecoration(nVar);
        return this;
    }

    public Banner addItemDecoration(RecyclerView.n nVar, int i5) {
        getViewPager2().addItemDecoration(nVar, i5);
        return this;
    }

    public Banner addOnPageChangeListener(OnPageChangeListener onPageChangeListener) {
        this.mOnPageChangeListener = onPageChangeListener;
        return this;
    }

    public Banner addPageTransformer(@k0 ViewPager2.PageTransformer pageTransformer) {
        this.mCompositePageTransformer.addTransformer(pageTransformer);
        return this;
    }

    public void destroy() {
        if (getViewPager2() != null && this.mPageChangeCallback != null) {
            getViewPager2().unregisterOnPageChangeCallback(this.mPageChangeCallback);
            this.mPageChangeCallback = null;
        }
        stop();
    }

    @Override // android.view.ViewGroup, android.view.View
    protected void dispatchDraw(Canvas canvas) {
        if (this.mBannerRadius <= 0.0f) {
            super.dispatchDraw(canvas);
            return;
        }
        canvas.saveLayer(new RectF(0.0f, 0.0f, canvas.getWidth(), canvas.getHeight()), this.mImagePaint, 31);
        super.dispatchDraw(canvas);
        drawTopLeft(canvas);
        drawTopRight(canvas);
        drawBottomLeft(canvas);
        drawBottomRight(canvas);
        canvas.restore();
    }

    @Override // android.view.ViewGroup, android.view.View
    public boolean dispatchTouchEvent(MotionEvent motionEvent) {
        if (!getViewPager2().isUserInputEnabled()) {
            return super.dispatchTouchEvent(motionEvent);
        }
        int actionMasked = motionEvent.getActionMasked();
        if (actionMasked == 1 || actionMasked == 3 || actionMasked == 4) {
            start();
        } else if (actionMasked == 0) {
            stop();
        }
        return super.dispatchTouchEvent(motionEvent);
    }

    public BA getAdapter() {
        if (this.mAdapter == null) {
            LogUtils.e(getContext().getString(R.string.banner_adapter_use_error));
        }
        return this.mAdapter;
    }

    public int getCurrentItem() {
        return getViewPager2().getCurrentItem();
    }

    public Indicator getIndicator() {
        if (this.mIndicator == null) {
            LogUtils.e(getContext().getString(R.string.indicator_null_error));
        }
        return this.mIndicator;
    }

    public IndicatorConfig getIndicatorConfig() {
        if (getIndicator() != null) {
            return getIndicator().getIndicatorConfig();
        }
        return null;
    }

    public int getItemCount() {
        if (getAdapter() == null) {
            return 0;
        }
        return getAdapter().getItemCount();
    }

    public int getRealCount() {
        return getAdapter().getRealCount();
    }

    public int getScrollTime() {
        return this.mScrollTime;
    }

    public ViewPager2 getViewPager2() {
        return this.mViewPager2;
    }

    public Banner isAutoLoop(boolean z5) {
        this.mIsAutoLoop = z5;
        return this;
    }

    public boolean isInfiniteLoop() {
        return this.mIsInfiniteLoop;
    }

    @Override // android.view.ViewGroup, android.view.View
    protected void onAttachedToWindow() {
        super.onAttachedToWindow();
        start();
    }

    @Override // com.youth.banner.util.BannerLifecycleObserver
    public void onDestroy(p pVar) {
        destroy();
    }

    @Override // android.view.ViewGroup, android.view.View
    protected void onDetachedFromWindow() {
        super.onDetachedFromWindow();
        stop();
    }

    /* JADX WARN: Code restructure failed: missing block: B:12:0x001e, code lost:
    
        if (r0 != 3) goto L33;
     */
    @Override // android.view.ViewGroup
    /*
        Code decompiled incorrectly, please refer to instructions dump.
    */
    public boolean onInterceptTouchEvent(MotionEvent motionEvent) {
        ViewParent parent;
        if (!getViewPager2().isUserInputEnabled() || !this.isIntercept) {
            return super.onInterceptTouchEvent(motionEvent);
        }
        int action = motionEvent.getAction();
        boolean z5 = true;
        if (action != 0) {
            if (action != 1) {
                if (action == 2) {
                    float x5 = motionEvent.getX();
                    float y5 = motionEvent.getY();
                    float abs = Math.abs(x5 - this.mStartX);
                    float abs2 = Math.abs(y5 - this.mStartY);
                    if (getViewPager2().getOrientation() != 0 ? abs2 <= this.mTouchSlop || abs2 <= abs : abs <= this.mTouchSlop || abs <= abs2) {
                        z5 = false;
                    }
                    this.mIsViewPager2Drag = z5;
                    parent = getParent();
                    z5 = this.mIsViewPager2Drag;
                }
            }
            getParent().requestDisallowInterceptTouchEvent(false);
            return super.onInterceptTouchEvent(motionEvent);
        }
        this.mStartX = motionEvent.getX();
        this.mStartY = motionEvent.getY();
        parent = getParent();
        parent.requestDisallowInterceptTouchEvent(z5);
        return super.onInterceptTouchEvent(motionEvent);
    }

    @Override // com.youth.banner.util.BannerLifecycleObserver
    public void onStart(p pVar) {
        start();
    }

    @Override // com.youth.banner.util.BannerLifecycleObserver
    public void onStop(p pVar) {
        stop();
    }

    public Banner removeIndicator() {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            removeView(indicator.getIndicatorView());
        }
        return this;
    }

    public Banner removeTransformer(ViewPager2.PageTransformer pageTransformer) {
        this.mCompositePageTransformer.removeTransformer(pageTransformer);
        return this;
    }

    public Banner setAdapter(BA ba) {
        if (ba == null) {
            throw new NullPointerException(getContext().getString(R.string.banner_adapter_null_error));
        }
        this.mAdapter = ba;
        if (!isInfiniteLoop()) {
            this.mAdapter.setIncreaseCount(0);
        }
        this.mAdapter.registerAdapterDataObserver(this.mAdapterDataObserver);
        this.mViewPager2.setAdapter(ba);
        setCurrentItem(this.mStartPosition, false);
        initIndicator();
        return this;
    }

    public Banner setAdapter(BA ba, boolean z5) {
        this.mIsInfiniteLoop = z5;
        setInfiniteLoop();
        setAdapter(ba);
        return this;
    }

    public Banner setBannerGalleryEffect(int i5, int i6) {
        return setBannerGalleryEffect(i5, i6, 0.85f);
    }

    public Banner setBannerGalleryEffect(int i5, int i6, float f5) {
        return setBannerGalleryEffect(i5, i5, i6, f5);
    }

    public Banner setBannerGalleryEffect(int i5, int i6, int i7) {
        return setBannerGalleryEffect(i5, i6, i7, 0.85f);
    }

    public Banner setBannerGalleryEffect(int i5, int i6, int i7, float f5) {
        if (i7 > 0) {
            addPageTransformer(new MarginPageTransformer((int) BannerUtils.dp2px(i7)));
        }
        if (f5 < 1.0f && f5 > 0.0f) {
            addPageTransformer(new ScaleInTransformer(f5));
        }
        setRecyclerViewPadding(i5 > 0 ? (int) BannerUtils.dp2px(i5 + i7) : 0, i6 > 0 ? (int) BannerUtils.dp2px(i6 + i7) : 0);
        return this;
    }

    public Banner setBannerGalleryMZ(int i5) {
        return setBannerGalleryMZ(i5, 0.88f);
    }

    public Banner setBannerGalleryMZ(int i5, float f5) {
        if (f5 < 1.0f && f5 > 0.0f) {
            addPageTransformer(new MZScaleInTransformer(f5));
        }
        setRecyclerViewPadding((int) BannerUtils.dp2px(i5));
        return this;
    }

    public Banner setBannerRound(float f5) {
        this.mBannerRadius = f5;
        return this;
    }

    @o0(api = 21)
    public Banner setBannerRound2(float f5) {
        BannerUtils.setBannerRound(this, f5);
        return this;
    }

    public Banner setCurrentItem(int i5) {
        return setCurrentItem(i5, true);
    }

    public Banner setCurrentItem(int i5, boolean z5) {
        getViewPager2().setCurrentItem(i5, z5);
        return this;
    }

    public Banner setDatas(List<T> list) {
        if (getAdapter() != null) {
            getAdapter().setDatas(list);
            getAdapter().notifyDataSetChanged();
            setCurrentItem(this.mStartPosition, false);
            setIndicatorPageChange();
            start();
        }
        return this;
    }

    public Banner setIndicator(Indicator indicator) {
        return setIndicator(indicator, true);
    }

    public Banner setIndicator(Indicator indicator, boolean z5) {
        removeIndicator();
        indicator.getIndicatorConfig().setAttachToBanner(z5);
        this.mIndicator = indicator;
        initIndicator();
        return this;
    }

    public Banner setIndicatorGravity(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null && indicator.getIndicatorConfig().isAttachToBanner()) {
            this.mIndicator.getIndicatorConfig().setGravity(i5);
            this.mIndicator.getIndicatorView().postInvalidate();
        }
        return this;
    }

    public Banner<T, BA> setIndicatorHeight(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setHeight(i5);
        }
        return this;
    }

    public Banner setIndicatorMargins(IndicatorConfig.Margins margins) {
        Indicator indicator = this.mIndicator;
        if (indicator != null && indicator.getIndicatorConfig().isAttachToBanner()) {
            this.mIndicator.getIndicatorConfig().setMargins(margins);
            this.mIndicator.getIndicatorView().requestLayout();
        }
        return this;
    }

    public Banner setIndicatorNormalColor(@l int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setNormalColor(i5);
        }
        return this;
    }

    public Banner setIndicatorNormalColorRes(@n int i5) {
        setIndicatorNormalColor(h.e(getContext(), i5));
        return this;
    }

    public Banner setIndicatorNormalWidth(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setNormalWidth(i5);
        }
        return this;
    }

    public Banner setIndicatorPageChange() {
        if (this.mIndicator != null) {
            this.mIndicator.onPageChanged(getRealCount(), BannerUtils.getRealPosition(isInfiniteLoop(), getCurrentItem(), getRealCount()));
        }
        return this;
    }

    public Banner<T, BA> setIndicatorRadius(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setRadius(i5);
        }
        return this;
    }

    public Banner setIndicatorSelectedColor(@l int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setSelectedColor(i5);
        }
        return this;
    }

    public Banner setIndicatorSelectedColorRes(@n int i5) {
        setIndicatorSelectedColor(h.e(getContext(), i5));
        return this;
    }

    public Banner setIndicatorSelectedWidth(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setSelectedWidth(i5);
        }
        return this;
    }

    public Banner setIndicatorSpace(int i5) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setIndicatorSpace(i5);
        }
        return this;
    }

    public Banner setIndicatorWidth(int i5, int i6) {
        Indicator indicator = this.mIndicator;
        if (indicator != null) {
            indicator.getIndicatorConfig().setNormalWidth(i5);
            this.mIndicator.getIndicatorConfig().setSelectedWidth(i6);
        }
        return this;
    }

    public Banner setIntercept(boolean z5) {
        this.isIntercept = z5;
        return this;
    }

    public Banner setLoopTime(long j5) {
        this.mLoopTime = j5;
        return this;
    }

    public Banner setOnBannerListener(OnBannerListener onBannerListener) {
        if (getAdapter() != null) {
            getAdapter().setOnBannerListener(onBannerListener);
        }
        return this;
    }

    public Banner setOrientation(int i5) {
        getViewPager2().setOrientation(i5);
        return this;
    }

    public Banner setPageTransformer(@k0 ViewPager2.PageTransformer pageTransformer) {
        getViewPager2().setPageTransformer(pageTransformer);
        return this;
    }

    public Banner setScrollTime(int i5) {
        this.mScrollTime = i5;
        return this;
    }

    public Banner setStartPosition(int i5) {
        this.mStartPosition = i5;
        return this;
    }

    public Banner setTouchSlop(int i5) {
        this.mTouchSlop = i5;
        return this;
    }

    public Banner setUserInputEnabled(boolean z5) {
        getViewPager2().setUserInputEnabled(z5);
        return this;
    }

    public Banner start() {
        if (this.mIsAutoLoop) {
            stop();
            postDelayed(this.mLoopTask, this.mLoopTime);
        }
        return this;
    }

    public Banner stop() {
        if (this.mIsAutoLoop) {
            removeCallbacks(this.mLoopTask);
        }
        return this;
    }
}
