/** 3D coverflow banner: side slides recede, then enlarge into focus on switch. */
(function () {
    const root = document.getElementById('homeBanner');
    if (!root) return;

    const slides = Array.from(root.querySelectorAll('.coverflow-slide'));
    const indicators = Array.from(root.querySelectorAll('[data-slide-to]'));
    const prevButton = root.querySelector('.coverflow-prev');
    const nextButton = root.querySelector('.coverflow-next');
    const interval = Number(root.dataset.interval) || 5000;
    const positionClasses = ['is-active', 'is-prev', 'is-next', 'is-far-prev', 'is-far-next'];
    let active = 0;
    let timer = null;
    let pointerStartX = null;

    function relativeOffset(index) {
        let offset = (index - active + slides.length) % slides.length;
        if (offset > slides.length / 2) offset -= slides.length;
        return offset;
    }

    function render() {
        slides.forEach(function (slide, index) {
            slide.classList.remove.apply(slide.classList, positionClasses);
            const offset = relativeOffset(index);
            if (offset === 0) slide.classList.add('is-active');
            else if (offset === -1) slide.classList.add('is-prev');
            else if (offset === 1) slide.classList.add('is-next');
            else if (offset < -1) slide.classList.add('is-far-prev');
            else slide.classList.add('is-far-next');
            slide.setAttribute('aria-hidden', offset === 0 ? 'false' : 'true');
        });
        indicators.forEach(function (indicator, index) {
            const selected = index === active;
            indicator.classList.toggle('active', selected);
            if (selected) indicator.setAttribute('aria-current', 'true');
            else indicator.removeAttribute('aria-current');
        });
    }

    function goTo(index, restart) {
        active = (index + slides.length) % slides.length;
        render();
        if (restart !== false) startAutoPlay();
    }

    function startAutoPlay() {
        window.clearInterval(timer);
        if (slides.length > 1 && !window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            timer = window.setInterval(function () { goTo(active + 1, false); }, interval);
        }
    }

    if (prevButton) prevButton.addEventListener('click', function () { goTo(active - 1); });
    if (nextButton) nextButton.addEventListener('click', function () { goTo(active + 1); });
    indicators.forEach(function (indicator) {
        indicator.addEventListener('click', function () { goTo(Number(indicator.dataset.slideTo)); });
    });
    slides.forEach(function (slide, index) {
        slide.addEventListener('click', function () {
            if (index !== active) goTo(index);
        });
    });

    root.addEventListener('mouseenter', function () { window.clearInterval(timer); });
    root.addEventListener('mouseleave', startAutoPlay);
    root.addEventListener('focusin', function () { window.clearInterval(timer); });
    root.addEventListener('focusout', startAutoPlay);
    root.addEventListener('keydown', function (event) {
        if (event.key === 'ArrowLeft') goTo(active - 1);
        if (event.key === 'ArrowRight') goTo(active + 1);
    });
    root.addEventListener('pointerdown', function (event) {
        if (event.pointerType !== 'mouse') pointerStartX = event.clientX;
    });
    root.addEventListener('pointerup', function (event) {
        if (pointerStartX === null) return;
        const distance = event.clientX - pointerStartX;
        pointerStartX = null;
        if (Math.abs(distance) > 45) goTo(active + (distance < 0 ? 1 : -1));
    });

    root.tabIndex = 0;
    render();
    startAutoPlay();
})();
