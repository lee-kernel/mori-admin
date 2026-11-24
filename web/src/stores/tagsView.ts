import { defineStore } from 'pinia'
import type { RouteLocationNormalizedLoaded } from 'vue-router'

export interface TagView {
  fullPath: string
  path: string
  name?: string
  title: string
}

function isDisplayableRoute(route: RouteLocationNormalizedLoaded) {
  return Boolean(route.meta?.title) && route.path !== '/404'
}

export const useTagsViewStore = defineStore('tagsView', {
  state: () => ({
    visitedViews: [] as TagView[],
  }),

  actions: {
    addVisitedView(route: RouteLocationNormalizedLoaded) {
      if (!isDisplayableRoute(route)) return

      const fullPath = route.fullPath || route.path
      if (this.visitedViews.some((view) => view.fullPath === fullPath)) return

      this.visitedViews.push({
        fullPath,
        path: route.path,
        name: typeof route.name === 'string' ? route.name : undefined,
        title: String(route.meta?.title),
      })
    },

    delVisitedView(fullPath: string) {
      this.visitedViews = this.visitedViews.filter((view) => view.fullPath !== fullPath)
      return [...this.visitedViews]
    },

    clearVisitedViews() {
      this.visitedViews = []
    },
  },
})
