document.querySelectorAll('.carousel').forEach((carousel) => {
    const prevBtn = carousel.parentElement.querySelector('.prev');
    const nextBtn = carousel.parentElement.querySelector('.next');
  
    prevBtn.addEventListener('click', () => {
      carousel.scrollBy({ left: -carousel.offsetWidth, behavior: 'smooth' });
    });
    nextBtn.addEventListener('click', () => {
      carousel.scrollBy({ left: carousel.offsetWidth, behavior: 'smooth' });
    });
  });

  // js/carousel.js

// A curated list of 15 movies + their TMDB poster URLs
const MOVIES = [
    { title: "The Shawshank Redemption", poster: "https://image.tmdb.org/t/p/w500/q6y0Go1tsGEsmtFryDOJo3dEmqu.jpg" },
    { title: "Fight Club",                  poster: "https://image.tmdb.org/t/p/w500/a26cQPRhJPX6GbWfQbvZdrrp9j9.jpg" },
    { title: "The Godfather",               poster: "https://image.tmdb.org/t/p/w500/3bhkrj58Vtu7enYsRolD1fZdja1.jpg" },
    { title: "The Dark Knight",             poster: "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg" },
    { title: "Pulp Fiction",                poster: "https://image.tmdb.org/t/p/w500/d5iIlFn5s0ImszYzBPb8JPIfbXD.jpg" },
    { title: "Inception",                   poster: "https://image.tmdb.org/t/p/w500/qmDpIHrmpJINaRKAfWQfftjCdyi.jpg" },
    { title: "Interstellar",                poster: "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg" },
    { title: "The Matrix",                  poster: "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg" },
    { title: "LOTR: Return of the King",    poster: "https://image.tmdb.org/t/p/w500/rCzpDGLbOoPwLjy3OAm5NUPOTrC.jpg" },
    { title: "Schindler’s List",            poster: "https://image.tmdb.org/t/p/w500/sF1U4EUQS8YHUYjNl3pMGNIQyr0.jpg" },
    { title: "Forrest Gump",                poster: "https://image.tmdb.org/t/p/w500/yE5d3BUhE8hCnkMUJOo1QDoOGNz.jpg" },
    { title: "The Lion King",               poster: "https://image.tmdb.org/t/p/w500/sKCr78MXSLixwmZ8DyJLrpMsd15.jpg" },
    { title: "The Avengers",                poster: "https://image.tmdb.org/t/p/w500/cezWGskPY5x7GaglTTRN4Fugfb8.jpg" },
    { title: "Avengers: Infinity War",      poster: "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg" },
    { title: "Avengers: Endgame",           poster: "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg" }
  ];
  
  // Builds a carousel given a selector and a movie list
  function buildCarousel(selector, movies) {
    const container = document.querySelector(selector + ' .carousel');
    movies.forEach(m => {
      const card = document.createElement('div');
      card.className = 'flex-shrink-0 w-40 hover:scale-105 transition';
      card.innerHTML = `<img src="${m.poster}" alt="${m.title}" class="rounded-lg" />`;
      container.appendChild(card);
    });
  }
  
  // Once DOM’s ready, inject into your “.carousel-section-1”
  document.addEventListener('DOMContentLoaded', () => {
    buildCarousel('.carousel-section-1', MOVIES);
  });
  
  