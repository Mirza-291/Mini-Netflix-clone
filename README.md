# 🎬 Mini Netflix Clone

> A full-stack web application replicating core Netflix functionality with semantic search, watch-lists, analytics, and admin tooling.

**Author:** Suhas 

---

## 🚀 Project Overview

The Mini Netflix Clone is a proof-of-concept platform enabling users to explore a rich media library of movies and TV shows. It features:
- Semantic search across metadata, cast, and genres
- Personalized watch-lists with LLM-based and cast-based recommendations
- Admin CRUD operations with poster uploads
- An interactive visualization dashboard with Chart.js
- Email-based auth (sign-up/login/password change)


## 🚀 Future Enhancements

> Plan to refactor the entire codebase using React for the frontend and Node.js with TypeScript for the backend.
> Plan to acheive Scalable, Reliable, fault tolerant system design.
> Plan to build on aws using services like EKS, ECR, API gateway, load balancer, autoscaling, route 53, lambda, dynamodb, kenesis, and so on.
---

## 👨‍💻 Team

| Member                 | Role / Contribution                              |
|------------------------|--------------------------------------------------|
| Suhas               | Sole Developer – architecture, code, UI/UX, testing |

---

## 🧠 Core Features

- 🎯 **Semantic Search:** Full-text + FAISS embedding re-rank across collections
- 📑 **Watch-List:** Save titles, get shared-cast & GPT-4 powered recs
- 🌐 **Language & Genre Explorer:** Interactive carousels with TMDB poster fallback
- 🛠 **Admin CRUD:** Insert/update/delete movies, TV shows, and cast info
- 📊 **Analytics Dashboard:** 6+ MongoDB aggregations visualized with Chart.js
- 🔐 **Authentication:** Email sign-up/login and password management

---

## 🛠️ Tech Stack

| Layer       | Tech Used                                       |
|-------------|-------------------------------------------------|
| Front-end   | HTML5, Tailwind CSS, Vanilla JS, Chart.js       |
| Back-end    | Django 4                                        |
| Database    | MongoDB 7 (with Djongo ORM)                     |
| ML & Search | Sentence Transformers, FAISS, OpenAI GPT-4,groq |
| APIs        | TMDB REST API, API endpoints                    |
| DevOps      | Docker, Git/GitHub                              |
| Hosting     | GCP VM (during development)                     |

---

## 🔌 API Endpoints

### `/search?q=<query>`
- Combines BM25 recall with FAISS semantic re-rank
- Aggregates from movies, TV shows, genres, cast, and watch-list

### `/browsebylanguage?lang=<iso-code>`
- Shows 5 movies, 5 shows, 5 watch-list items for a language

### `/mylist`
- Watch-list dashboard with:
  - Shared-cast recommendations
  - LLM-based recommendations
  - Popularity fallback suggestions

### `/new-and-popular?genre=<genre>`
- Genre trends with cast enrichment and personalized highlights

### `/crud`
- Admin page for CRUD operations across collections with image uploads

### `/detail/<title>`
- Full data fetch with TMDB fallback for missing info

### `/visualization?query=<type>`
- 7 chart types available:
  - `top_actors`
  - `top_directors`
  - `avg_runtime`
  - `yearly_stats`
  - `actor_coappearances`
  - `top3_movies`

---

## 📊 Visualization Dashboard

Implemented using MongoDB Aggregations and Python fallbacks. Supports:

- 📌 Top actors by appearance
- 🎬 Top directors by revenue
- ⏱️ Average runtime per genre
- 📈 Yearly content statistics
- 🤝 Actor co-appearances
- 🏆 Top-3 movies by director

---

## 🖥️ UI Snapshots

- Landing page
- Hero & carousel home screen
- TV Shows, Movies, and New & Popular pages
- My List and Browse by Language views
- Admin CRUD panel
- Login / Sign-up / Change Password screens
- Visualization dashboard
- Semantic search results page

---

## 🧪 Note

> This repo contains only select code snippets and endpoints. The full project spans over 2000+ lines of code with comprehensive queries and components.

---

## 📎 License

This project is for educational/demo purposes and is not affiliated with Netflix Inc.

---
