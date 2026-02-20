export type AuthUser = {
  id: string
  username: string
  email: string
  role: "admin" | "user"
}
