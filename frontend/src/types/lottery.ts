/** 彩券遊戲種類 */
export interface LotteryGame {
  id: number
  code: string
  name: string
  main_pool_size: number
  main_pick_count: number
  has_special: boolean
  special_pool_size: number | null
  draw_schedule: string
  is_active: boolean
}

/** 開獎紀錄 */
export interface DrawResult {
  id: number
  game: number
  game_name: string
  game_code: string
  draw_term: string
  draw_date: string
  numbers_ordered: number[]
  numbers_sorted: number[]
  special_number: number | null
  total_sales: number | null
}

/** 號碼頻率統計 */
export interface NumberFrequency {
  number: number
  count: number
  percentage: number
}

/** 遺漏值統計 */
export interface MissingValue {
  number: number
  missing_draws: number
  last_appeared: string
}

/** API 分頁回應 */
export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
