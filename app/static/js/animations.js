/**
 * Advanced Animation and Effects Module
 * Provides scroll animations, particle effects, and modern UI transitions
 */

// ============================================================================
// SCROLL REVEAL ANIMATIONS
// ============================================================================

export function initScrollAnimations() {
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-in');
        
        // Add stagger delay for children
        const children = entry.target.querySelectorAll('[data-animate-child]');
        children.forEach((child, index) => {
          child.style.animationDelay = `${index * 100}ms`;
          child.classList.add('animate-in');
        });
      }
    });
  }, observerOptions);

  // Observe elements with data-animate attribute
  document.querySelectorAll('[data-animate]').forEach(el => {
    observer.observe(el);
  });
}

// ============================================================================
// PARTICLE BACKGROUND
// ============================================================================

export function createParticleBackground(containerId = 'particle-container') {
  const container = document.getElementById(containerId);
  if (!container) return;

  const particleCount = 50;
  const particles = [];

  for (let i = 0; i < particleCount; i++) {
    const particle = document.createElement('div');
    particle.className = 'particle';
    
    // Random properties
    const size = Math.random() * 4 + 2;
    const x = Math.random() * 100;
    const y = Math.random() * 100;
    const duration = Math.random() * 20 + 10;
    const delay = Math.random() * 5;
    
    particle.style.cssText = `
      width: ${size}px;
      height: ${size}px;
      left: ${x}%;
      top: ${y}%;
      animation: float ${duration}s ease-in-out ${delay}s infinite;
    `;
    
    container.appendChild(particle);
    particles.push(particle);
  }

  return particles;
}

// ============================================================================
// MAGNETIC BUTTON EFFECT
// ============================================================================

export function initMagneticButtons() {
  const buttons = document.querySelectorAll('[data-magnetic]');
  
  buttons.forEach(button => {
    button.addEventListener('mousemove', (e) => {
      const rect = button.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const deltaX = (x - centerX) / centerX;
      const deltaY = (y - centerY) / centerY;
      
      const moveX = deltaX * 10;
      const moveY = deltaY * 10;
      
      button.style.transform = `translate(${moveX}px, ${moveY}px)`;
    });
    
    button.addEventListener('mouseleave', () => {
      button.style.transform = 'translate(0, 0)';
    });
  });
}

// ============================================================================
// TYPING EFFECT
// ============================================================================

export function typeWriter(elementId, text, speed = 50) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  let i = 0;
  element.textContent = '';
  
  function type() {
    if (i < text.length) {
      element.textContent += text.charAt(i);
      i++;
      setTimeout(type, speed);
    }
  }
  
  type();
}

// ============================================================================
// PARALLAX SCROLL
// ============================================================================

export function initParallaxScroll() {
  const parallaxElements = document.querySelectorAll('[data-parallax]');
  
  window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    
    parallaxElements.forEach(el => {
      const speed = el.dataset.parallax || 0.5;
      const yPos = -(scrolled * speed);
      el.style.transform = `translateY(${yPos}px)`;
    });
  });
}

// ============================================================================
// RIPPLE EFFECT
// ============================================================================

export function addRippleEffect(button) {
  button.addEventListener('click', function(e) {
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    
    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    
    this.appendChild(ripple);
    
    setTimeout(() => ripple.remove(), 600);
  });
}

export function initRippleButtons() {
  document.querySelectorAll('[data-ripple]').forEach(addRippleEffect);
}

// ============================================================================
// CARD TILT EFFECT
// ============================================================================

export function initCardTilt() {
  const cards = document.querySelectorAll('[data-tilt]');
  
  cards.forEach(card => {
    card.addEventListener('mousemove', (e) => {
      const rect = card.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;
      
      const rotateX = ((y - centerY) / centerY) * -10;
      const rotateY = ((x - centerX) / centerX) * 10;
      
      card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.02, 1.02, 1.02)`;
    });
    
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale3d(1, 1, 1)';
    });
  });
}

// ============================================================================
// COUNTER ANIMATION
// ============================================================================

export function animateCounter(elementId, target, duration = 2000) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  const start = 0;
  const increment = target / (duration / 16);
  let current = start;
  
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      current = target;
      clearInterval(timer);
    }
    element.textContent = Math.floor(current);
  }, 16);
}

// ============================================================================
// GRADIENT ANIMATION
// ============================================================================

export function animateGradient(elementId) {
  const element = document.getElementById(elementId);
  if (!element) return;
  
  let angle = 0;
  
  setInterval(() => {
    angle = (angle + 1) % 360;
    element.style.background = `linear-gradient(${angle}deg, 
      rgba(94, 242, 197, 0.1), 
      rgba(124, 248, 255, 0.15), 
      rgba(158, 247, 123, 0.1))`;
  }, 50);
}

// ============================================================================
// INITIALIZE ALL ANIMATIONS
// ============================================================================

export function initAllAnimations() {
  initScrollAnimations();
  initMagneticButtons();
  initParallaxScroll();
  initRippleButtons();
  initCardTilt();
}

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAllAnimations);
} else {
  initAllAnimations();
}
