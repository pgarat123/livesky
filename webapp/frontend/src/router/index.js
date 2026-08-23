import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import DeviceDetailView from '../views/DeviceDetailView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      // le ":id" est un paramètre dynamique
      path: '/device/:id',
      name: 'device-detail',
      component: DeviceDetailView,
    },
    {
      path: '/historique',
      name: 'stats',
      component: () => import('../views/StatsView.vue'),
    },
    {
      path: '/previsions',
      name: 'forecast',
      component: () => import('../views/ForecastView.vue'),
    },
    {
      path: '/admin',
      name: 'admin',
      component: () => import('../views/AdminView.vue'),
    },
  ],
})

export default router
