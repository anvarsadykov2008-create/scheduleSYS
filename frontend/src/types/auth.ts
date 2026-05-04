export const UserRole = {
    ADMIN: "администратор",
    DISPATCHER: "диспетчер",
    TEACHER: "преподаватель",
    STUDENT: "студент",
    MANAGEMENT: "администрация"
} as const;

export type UserRole = typeof UserRole[keyof typeof UserRole];

export interface User {
    id: number;
    username: string;
    role: UserRole;
    teacher_id?: number;
    group_id?: number;
    full_name?: string;
}
