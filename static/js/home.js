(function () {
  'use strict';

  // ================================================================
  // 1. LOADING SCREEN
  // ================================================================
  function initLoading() {
    var loader = document.querySelector('.home-loading');
    if (!loader) return;
    window.addEventListener('load', function () {
      setTimeout(function () {
        loader.classList.add('hidden');
        document.body.style.overflow = '';
      }, 800);
    });
    setTimeout(function () {
      if (!loader.classList.contains('hidden')) {
        loader.classList.add('hidden');
        document.body.style.overflow = '';
      }
    }, 4000);
  }

  // ================================================================
  // 2. SCROLL PROGRESS BAR
  // ================================================================
  function initScrollProgress() {
    var bar = document.querySelector('.scroll-progress');
    if (!bar) return;
    window.addEventListener('scroll', function () {
      var scrollTop = window.scrollY;
      var docHeight = document.documentElement.scrollHeight - window.innerHeight;
      var progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
      bar.style.width = progress + '%';
    });
  }

  // ================================================================
  // 3. NAVBAR SCROLL EFFECT
  // ================================================================
  function initNavbar() {
    var header = document.querySelector('.home-header');
    if (!header) return;
    function updateNav() {
      if (window.scrollY > 60) {
        header.classList.add('scrolled');
      } else {
        header.classList.remove('scrolled');
      }
    }
    window.addEventListener('scroll', updateNav, { passive: true });
    updateNav();
  }

  // ================================================================
  // 4. MOBILE HAMBURGER
  // ================================================================
  function initMobileMenu() {
    var hamburger = document.querySelector('.hamburger');
    var navMenu = document.getElementById('navMenu');
    if (!hamburger || !navMenu) return;

    hamburger.addEventListener('click', function () {
      navMenu.classList.toggle('active');
      hamburger.classList.toggle('active');
    });

    document.querySelectorAll('.nav-link').forEach(function (link) {
      link.addEventListener('click', function () {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
      });
    });

    document.addEventListener('click', function (e) {
      if (!e.target.closest('.header-container')) {
        navMenu.classList.remove('active');
        hamburger.classList.remove('active');
      }
    });
  }

  // ================================================================
  // 5. CUSTOM CURSOR
  // ================================================================
  function initCursor() {
    var cursor = document.querySelector('.home-cursor');
    var dot = document.querySelector('.home-cursor-dot');
    if (!cursor || !dot) return;

    var posX = 0, posY = 0, mouseX = 0, mouseY = 0;

    document.addEventListener('mousemove', function (e) {
      mouseX = e.clientX;
      mouseY = e.clientY;
      dot.style.left = mouseX + 'px';
      dot.style.top = mouseY + 'px';
    });

    function animate() {
      posX += (mouseX - posX) * 0.15;
      posY += (mouseY - posY) * 0.15;
      cursor.style.left = posX + 'px';
      cursor.style.top = posY + 'px';
      requestAnimationFrame(animate);
    }
    animate();

    document.querySelectorAll('a, button, .btn-primary, .btn-outline, .valor-card, .nivel-card, .mv-card, .evento-card, .galeria-item').forEach(function (el) {
      el.addEventListener('mouseenter', function () { cursor.classList.add('hovering'); });
      el.addEventListener('mouseleave', function () { cursor.classList.remove('hovering'); });
    });
  }

  // ================================================================
  // 6. HERO PARTICLES
  // ================================================================
  function initHeroParticles() {
    var container = document.querySelector('.hero-particles');
    if (!container) return;
    var count = window.innerWidth < 768 ? 15 : 30;
    for (var i = 0; i < count; i++) {
      var p = document.createElement('div');
      p.className = 'hero-particle';
      var size = 4 + Math.random() * 12;
      p.style.width = size + 'px';
      p.style.height = size + 'px';
      p.style.left = Math.random() * 100 + '%';
      p.style.animationDuration = (15 + Math.random() * 25) + 's';
      p.style.animationDelay = (Math.random() * 20) + 's';
      container.appendChild(p);
    }
  }

  // ================================================================
  // 7. TYPEWRITER EFFECT
  // ================================================================
  function initTypewriter() {
    var el = document.querySelector('.hero-typewriter');
    if (!el) return;

    var phrases = [
      'Formamos líderes del mañana',
      'Excelencia académica con valores',
      'Innovación educativa constante',
      'Construyendo futuro con pasión'
    ];
    var phraseIndex = 0;
    var charIndex = 0;
    var isDeleting = false;
    var currentText = '';

    function type() {
      var currentPhrase = phrases[phraseIndex];

      if (isDeleting) {
        currentText = currentPhrase.substring(0, charIndex - 1);
        charIndex--;
      } else {
        currentText = currentPhrase.substring(0, charIndex + 1);
        charIndex++;
      }

      el.textContent = currentText;

      if (!isDeleting && charIndex === currentPhrase.length) {
        el.classList.add('typewriter-end');
        setTimeout(function () {
          el.classList.remove('typewriter-end');
          isDeleting = true;
          setTimeout(type, 300);
        }, 2000);
        return;
      }

      if (isDeleting && charIndex === 0) {
        isDeleting = false;
        phraseIndex = (phraseIndex + 1) % phrases.length;
        setTimeout(type, 400);
        return;
      }

      var speed = isDeleting ? 40 : 80;
      setTimeout(type, speed);
    }

    setTimeout(type, 1500);
  }

  // ================================================================
  // 8. COUNTER ANIMATION
  // ================================================================
  function initCounters() {
    var counters = document.querySelectorAll('.stat-number');
    if (!counters.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          var target = entry.target;
          var text = target.textContent.trim();
          var numMatch = text.match(/([\d.]+)/);
          var suffix = text.replace(/[\d.]+/, '');
          if (!numMatch) return;
          var finalValue = parseFloat(numMatch[1]);
          var isFloat = numMatch[1].indexOf('.') !== -1;
          var duration = 1500;
          var startTime = performance.now();

          function update(currentTime) {
            var elapsed = currentTime - startTime;
            var progress = Math.min(elapsed / duration, 1);
            var eased = 1 - Math.pow(1 - progress, 3);
            var current = eased * finalValue;
            target.textContent = (isFloat ? current.toFixed(1) : Math.floor(current)) + suffix;
            if (progress < 1) {
              requestAnimationFrame(update);
            } else {
              target.textContent = text;
            }
          }
          requestAnimationFrame(update);
          entry.target.closest('.stat-item').classList.add('animated');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.5 });

    counters.forEach(function (c) { observer.observe(c); });
  }

  // ================================================================
  // 9. INTERSECTION OBSERVER REVEAL
  // ================================================================
  function initReveal() {
    var els = document.querySelectorAll('.reveal-fade, .reveal-left, .reveal-right, .reveal-scale, .reveal-stagger');
    if (!els.length) return;

    var observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

    els.forEach(function (el) { observer.observe(el); });
  }

  // ================================================================
  // 10. 3D TILT ON CARDS
  // ================================================================
  function initTilt() {
    var cards = document.querySelectorAll('.tilt-card');
    if (!cards.length) return;

    cards.forEach(function (card) {
      card.addEventListener('mousemove', function (e) {
        var rect = card.getBoundingClientRect();
        var x = e.clientX - rect.left;
        var y = e.clientY - rect.top;
        var centerX = rect.width / 2;
        var centerY = rect.height / 2;
        var rotateX = ((y - centerY) / centerY) * -8;
        var rotateY = ((x - centerX) / centerX) * 8;
        card.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg)';
      });

      card.addEventListener('mouseleave', function () {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0)';
      });
    });
  }

  // ================================================================
  // 11. MAGNETIC BUTTONS
  // ================================================================
  function initMagnetic() {
    var btns = document.querySelectorAll('.magnetic-btn');
    if (!btns.length) return;

    btns.forEach(function (btn) {
      btn.addEventListener('mousemove', function (e) {
        var rect = btn.getBoundingClientRect();
        var x = e.clientX - rect.left - rect.width / 2;
        var y = e.clientY - rect.top - rect.height / 2;
        btn.style.transform = 'translate(' + (x * 0.2) + 'px, ' + (y * 0.2) + 'px)';
      });

      btn.addEventListener('mouseleave', function () {
        btn.style.transform = 'translate(0, 0)';
      });
    });
  }

  // ================================================================
  // 12. BUTTON RIPPLE EFFECT
  // ================================================================
  function initRipple() {
    document.querySelectorAll('.btn-primary, .btn-outline, .btn-aula').forEach(function (btn) {
      btn.addEventListener('click', function (e) {
        var rect = btn.getBoundingClientRect();
        var ripple = document.createElement('span');
        ripple.className = 'btn-ripple';
        var size = Math.max(rect.width, rect.height);
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = (e.clientX - rect.left - size / 2) + 'px';
        ripple.style.top = (e.clientY - rect.top - size / 2) + 'px';
        btn.appendChild(ripple);
        setTimeout(function () { ripple.remove(); }, 600);
      });
    });
  }

  // ================================================================
  // 13. BACK TO TOP
  // ================================================================
  function initBackToTop() {
    var btn = document.querySelector('.back-to-top');
    if (!btn) return;

    window.addEventListener('scroll', function () {
      if (window.scrollY > 500) {
        btn.classList.add('visible');
      } else {
        btn.classList.remove('visible');
      }
    }, { passive: true });

    btn.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  // ================================================================
  // 14. SMOOTH ANCHOR SCROLL
  // ================================================================
  function initAnchorScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(function (anchor) {
      anchor.addEventListener('click', function (e) {
        var targetId = anchor.getAttribute('href');
        if (targetId === '#') return;
        var target = document.querySelector(targetId);
        if (target) {
          e.preventDefault();
          var offset = 70;
          var targetPos = target.getBoundingClientRect().top + window.scrollY - offset;
          window.scrollTo({ top: targetPos, behavior: 'smooth' });
        }
      });
    });
  }

  // ================================================================
  // 15. FORM INTERACTION
  // ================================================================
  function initFormEffects() {
    document.querySelectorAll('.contacto-field input, .contacto-field textarea').forEach(function (input) {
      input.addEventListener('focus', function () {
        input.closest('.contacto-field').classList.add('focused');
      });
      input.addEventListener('blur', function () {
        input.closest('.contacto-field').classList.remove('focused');
        if (input.value.trim() !== '') {
          input.classList.add('filled');
        } else {
          input.classList.remove('filled');
        }
      });
      if (input.value.trim() !== '') {
        input.classList.add('filled');
      }
    });
  }

  // ================================================================
  // 16. PARALLAX ON SCROLL
  // ================================================================
  function initParallax() {
    var sections = document.querySelectorAll('.parallax-bg');
    if (!sections.length) return;

    window.addEventListener('scroll', function () {
      var scrollY = window.scrollY;
      sections.forEach(function (section) {
        var rect = section.getBoundingClientRect();
        if (rect.top < window.innerHeight && rect.bottom > 0) {
          var speed = 0.15;
          var offset = (rect.top * speed);
          section.style.backgroundPositionY = offset + 'px';
        }
      });
    }, { passive: true });
  }

  // ================================================================
  // 17. HERO 3D TILT
  // ================================================================
  function initHeroTilt() {
    var hero = document.querySelector('.hero-3d-tilt');
    if (!hero) return;

    hero.addEventListener('mousemove', function (e) {
      var rect = hero.getBoundingClientRect();
      var x = e.clientX - rect.left;
      var y = e.clientY - rect.top;
      var centerX = rect.width / 2;
      var centerY = rect.height / 2;
      var rotateX = ((y - centerY) / centerY) * -5;
      var rotateY = ((x - centerX) / centerX) * 5;
      hero.style.transform = 'perspective(1000px) rotateX(' + rotateX + 'deg) rotateY(' + rotateY + 'deg) translateZ(20px)';
    });

    hero.addEventListener('mouseleave', function () {
      hero.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateZ(0)';
      hero.style.transition = 'transform 0.6s ease';
      setTimeout(function () { hero.style.transition = ''; }, 600);
    });
  }

  // ================================================================
  // 18. STATS BUBBLE ANIMATION
  // ================================================================
  function initStatsBubbles() {
    var stats = document.querySelector('.home-stats');
    if (!stats) return;
    for (var i = 0; i < 8; i++) {
      var bubble = document.createElement('div');
      bubble.style.cssText =
        'position:absolute;border-radius:50%;background:rgba(99,179,237,0.04);' +
        'pointer-events:none;' +
        'width:' + (40 + Math.random() * 120) + 'px;' +
        'height:' + (40 + Math.random() * 120) + 'px;' +
        'left:' + (Math.random() * 100) + '%;' +
        'top:' + (Math.random() * 100) + '%;' +
        'animation:bubbleFloat ' + (8 + Math.random() * 12) + 's ease-in-out infinite;' +
        'animation-delay:' + (Math.random() * 5) + 's;';
      stats.appendChild(bubble);
    }
  }

  // ================================================================
  // INIT
  // ================================================================
  document.addEventListener('DOMContentLoaded', function () {
    initLoading();
    initScrollProgress();
    initNavbar();
    initMobileMenu();
    initCursor();
    initHeroParticles();
    initTypewriter();
    initCounters();
    initReveal();
    initTilt();
    initMagnetic();
    initRipple();
    initBackToTop();
    initAnchorScroll();
    initFormEffects();
    initParallax();
    initHeroTilt();
    initStatsBubbles();
  });

  // Add missing keyframe for stats bubbles
  var style = document.createElement('style');
  style.textContent = '@keyframes bubbleFloat { 0%, 100% { transform: translateY(0) scale(1); } 50% { transform: translateY(-20px) scale(1.05); } }';
  document.head.appendChild(style);

})();
