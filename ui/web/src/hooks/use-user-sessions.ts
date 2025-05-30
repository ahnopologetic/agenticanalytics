import { useQuery } from "@tanstack/react-query"
import { getUserSessions } from "../api"

const useUserSessions = (userId: string) => {
    return useQuery({
        queryKey: ['user-sessions', userId],
        queryFn: () => getUserSessions(userId),
        enabled: !!userId,
    })
}

export default useUserSessions