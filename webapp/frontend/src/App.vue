<script setup>
import { RouterLink, RouterView } from 'vue-router'
import VueFeather from 'vue-feather'
</script>

<template>
  <header class="site-header">
    <div class="site-header-inner">
      <RouterLink to="/" class="brand">
        <vue-feather type="cloud-drizzle" size="22"></vue-feather>
        <span>LiveSky</span>
      </RouterLink>
      <nav>
        <RouterLink to="/">Accueil</RouterLink>
        <RouterLink to="/historique">Historique</RouterLink>
        <RouterLink to="/previsions">Prévisions</RouterLink>
        <RouterLink to="/admin">Admin</RouterLink>
      </nav>
    </div>
  </header>

  <RouterView />
</template>

<style scoped>
.site-header {
  position: sticky;
  top: 0;
  z-index: 10;
  height: var(--header-height);
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-border);
}

.site-header-inner {
  max-width: 1100px;
  height: 100%;
  margin: 0 auto;
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
}

.brand {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: 700;
  font-size: 1.1rem;
  color: var(--color-heading);
  text-decoration: none;
  flex-shrink: 0;
}

nav {
  display: flex;
  gap: 0.25rem;
  overflow-x: auto;
}

nav a {
  padding: 0.5rem 0.85rem;
  border-radius: var(--radius-sm);
  color: var(--color-text-muted);
  text-decoration: none;
  font-size: 0.9rem;
  font-weight: 500;
  white-space: nowrap;
  transition: background-color 0.15s, color 0.15s;
}

nav a:hover {
  background: var(--color-surface-muted);
  color: var(--color-heading);
}

nav a.router-link-exact-active {
  background: var(--color-accent-soft);
  color: var(--color-accent);
}
</style>
