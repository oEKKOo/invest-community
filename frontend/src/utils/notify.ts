export const notifyError = async (message: string) => {
  try {
    const { ElMessage } = await import('element-plus')
    ElMessage.error(message)
  } catch {
    console.error(message)
  }
}
