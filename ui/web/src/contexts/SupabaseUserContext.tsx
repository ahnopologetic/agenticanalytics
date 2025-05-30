import type { User } from '@supabase/supabase-js'
import type { ReactNode } from 'react'
import { createContext, useEffect, useState } from 'react'
import { supabase } from '../supabaseClient'

interface SupabaseUserContextType {
    user: User | null
    loading: boolean
    error: string | null
}

export const SupabaseUserContext = createContext<SupabaseUserContextType | undefined>(undefined)

export const SupabaseUserProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let mounted = true
        const getUser = async () => {
            setLoading(true)
            try {
                const { data, error } = await supabase.auth.getUser()
                if (error) {
                    setError(error.message)
                    setUser(null)
                } else {
                    setUser(data.user)
                    setError(null)
                }
            } catch (err: unknown) {
                if (err instanceof Error) {
                    setError(err.message)
                } else {
                    setError('Unknown error')
                }
                setUser(null)
            } finally {
                setLoading(false)
            }
        }
        getUser()
        // Listen for auth state changes
        const { data: listener } = supabase.auth.onAuthStateChange((_event, session) => {
            if (!mounted) return
            setUser(session?.user ?? null)
        })
        return () => {
            mounted = false
            listener?.subscription.unsubscribe()
        }
    }, [])

    return (
        <SupabaseUserContext.Provider value={{ user, loading, error }}>
            {children}
        </SupabaseUserContext.Provider>
    )
}