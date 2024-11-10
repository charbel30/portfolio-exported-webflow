   // Page Transition Logic
   document.addEventListener('DOMContentLoaded', () => {
    const transitionPreloader = document.querySelector('.transition-preloader');
    const links = document.querySelectorAll('a[href]:not([target="_blank"])');

    links.forEach(link => {
      link.addEventListener('click', (e) => {
        const href = link.getAttribute('href');
        // Only handle internal links
        if (href.startsWith('/') || href.startsWith('./') || href.startsWith('../') || !href.startsWith('http')) {
          e.preventDefault();
          transitionPreloader.classList.add('active');
          
          setTimeout(() => {
            window.location.href = href;
          }, 500);
        }
      });
    });

    // Hide preloader when page loads
    window.addEventListener('load', () => {
      transitionPreloader.classList.remove('active');
    });
  });