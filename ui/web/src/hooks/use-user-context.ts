import { useContext } from 'react'
import { SupabaseUserContext } from '../contexts/SupabaseUserContext'

export const useUserContext = () => {
    const context = useContext(SupabaseUserContext)
    if (context === undefined) {
        throw new Error('useUserContext must be used within a SupabaseUserProvider')
    }
    return context
} 