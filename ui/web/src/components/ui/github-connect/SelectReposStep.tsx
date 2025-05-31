import { useState, useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import { getGithubRepos, getGithubOrgs, getGithubOrgRepos } from "../../../api";
import type { Repo, Org } from "../../../api";

type SelectReposStepProps = {
  selectedRepos: Repo[];
  onToggle: (repo: Repo) => void;
  onContinue: () => void;
};

const SelectReposStep = ({ selectedRepos, onToggle, onContinue }: SelectReposStepProps) => {
  const [selectedContext, setSelectedContext] = useState<string>("personal");
  const [search, setSearch] = useState("");
  const [displayCount, setDisplayCount] = useState(10);

  // Queries
  const { data: orgs, isLoading: orgsLoading } = useQuery<Org[]>({
    queryKey: ["github-orgs"],
    queryFn: getGithubOrgs,
  });
  const { data: personalRepos, isLoading: personalReposLoading } = useQuery<Repo[]>({
    queryKey: ["github-repos", "personal"],
    queryFn: getGithubRepos,
    staleTime: 1000 * 60 * 5,
  });
  const { data: orgRepos, isLoading: orgReposLoading } = useQuery<Repo[]>({
    queryKey: ["github-repos", selectedContext],
    queryFn: () => getGithubOrgRepos(selectedContext),
    enabled: selectedContext !== "personal",
    staleTime: 1000 * 60 * 5,
  });

  // Username for dropdown (from first personal repo owner)
  const username = useMemo(() => {
    if (personalRepos && personalRepos.length > 0) {
      return (personalRepos[0].owner?.login as string) || "Personal";
    }
    return "Personal";
  }, [personalRepos]);

  // Repo list for current context
  const repos = useMemo(() => {
    if (selectedContext === "personal") return personalRepos || [];
    return orgRepos || [];
  }, [selectedContext, personalRepos, orgRepos]);

  // Filtered repos
  const filteredRepos = useMemo(() => {
    if (!search) return repos;
    return repos.filter((repo) =>
      repo.name.toLowerCase().includes(search.toLowerCase())
    );
  }, [repos, search]);

  const displayedRepos = filteredRepos.slice(0, displayCount);
  const loadMore = () => setDisplayCount((prev) => Math.min(prev + 10, filteredRepos.length));

  return (
    <div className="w-96 bg-white rounded shadow p-6 max-h-[calc(100vh-10rem)] overflow-y-auto">
      <h2 className="text-lg font-semibold mb-4">Select repositories to scan</h2>
      {/* Context Dropdown */}
      <div className="mb-4 relative">
        <label htmlFor="context-select" className="sr-only">Select context</label>
        <select
          id="context-select"
          className="w-full border rounded px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={selectedContext}
          onChange={e => {
            setSelectedContext(e.target.value);
            setDisplayCount(10);
          }}
          aria-label="Select personal or organization context"
        >
          <option value="personal">{username} (Personal)</option>
          {orgs && orgs.map(org => (
            <option key={org.id} value={org.login}>{org.login}</option>
          ))}
        </select>
      </div>
      {/* Search Bar */}
      <input
        type="text"
        className="w-full border rounded px-3 py-2 mb-4 focus:outline-none focus:ring-2 focus:ring-blue-400"
        placeholder="Search repositories..."
        value={search}
        onChange={e => setSearch(e.target.value)}
        aria-label="Search repositories"
      />
      {/* Repo List */}
      <div className="max-h-80 overflow-y-auto mb-4">
        {(personalReposLoading || orgReposLoading || orgsLoading) ? (
          <div className="text-center py-8">Loading...</div>
        ) : (
          <ul>
            {displayedRepos.map(repo => (
              <li key={repo.id} className="mb-2 flex items-center">
                <input
                  id={`repo-${repo.id}`}
                  type="checkbox"
                  checked={selectedRepos.some(r => r.id === repo.id)}
                  onChange={() => onToggle(repo)}
                  className="mr-2"
                  aria-label={`Select ${repo.name}`}
                />
                <label htmlFor={`repo-${repo.id}`} className="cursor-pointer select-none">
                  {repo.name}
                </label>
              </li>
            ))}
          </ul>
        )}
        {displayCount < filteredRepos.length && (
          <button
            onClick={loadMore}
            className="w-full py-2 mt-2 text-sm text-blue-600 hover:text-blue-800"
          >
            Load more repositories...
          </button>
        )}
      </div>
      <button
        className="w-full py-2 rounded bg-blue-600 text-white font-semibold hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-400"
        onClick={onContinue}
        tabIndex={0}
        aria-label="Continue to label repositories"
        onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') onContinue() }}
        disabled={selectedRepos.length === 0}
      >
        Continue
      </button>
    </div>
  );
};

export default SelectReposStep;