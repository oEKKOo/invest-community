/// <reference types="vite/client" />
/// <reference types="vue/macros-global" />

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<{}, {}, any>
  export default component
}

// 修复 Vue 类型声明问题
declare global {
  // Vue Language Service 内部类型
  namespace __VLS_ {
    type WithComponent<T, K, U, M> = any;
    type intrinsicElements = any;
    type functionalComponentArgsRest<T> = any;
    type FunctionalComponentProps<T, K> = any;
    type elementAsFunctionalComponent<T> = any;
    type asFunctionalComponent<T> = any;
    type pickFunctionalComponentCtx<T, K> = any;
    type NormalizeEmits<T> = any;
  }
  
  // 全局类型声明
  const __VLS_WithComponent: any;
  const __VLS_intrinsicElements: any;
  const __VLS_functionalComponentArgsRest: any;
  const __VLS_FunctionalComponentProps: any;
  const __VLS_elementAsFunctionalComponent: any;
  const __VLS_asFunctionalComponent: any;
  const __VLS_pickFunctionalComponentCtx: any;
  const __VLS_NormalizeEmits: any;
}

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_TITLE: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}