import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

/**
 *  import { usePageUser } from "@/hooks/usePageUser";
 *  const { userName } = usePageUser();
 *  console.log("当前用户：", userName.value);
 */
export function usePageUser() {
  const route = useRoute()
  const userStore = useUserStore()

  const userName = computed(() => {
    const path = route.path

    if (path.startsWith('/single')) {
      return ''
    }

    return userStore.displayName || 'admin'
  })

  return {
    userName,
  }
}
