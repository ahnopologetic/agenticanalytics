import { saveGithubToken } from "../../api";
import { supabase } from "../../supabaseClient";
import { useNavigate } from "react-router-dom";

export default function GithubCallback() {
    const navigate = useNavigate();
    supabase.auth.onAuthStateChange(async (_, session) => {
        if (session) {
            if (session.provider_token && session.user.app_metadata.provider === 'github') {
                await saveGithubToken(session.provider_token);
            }
            navigate('/github-connect');
        }
    });
    return (<></>)
}