import { useState } from 'react';
import { useRepos, useTrackingPlanEvents, useCloneGithubRepo } from '../../hooks/api';

const RepoList = () => {
  const [selectedRepoId, setSelectedRepoId] = useState<string>('');
  
  // Fetch repositories
  const { 
    data: repos, 
    isLoading: isLoadingRepos, 
    error: reposError 
  } = useRepos();
  
  // Fetch tracking plan events for the selected repo
  const { 
    data: events, 
    isLoading: isLoadingEvents 
  } = useTrackingPlanEvents(selectedRepoId, !!selectedRepoId);
  
  // Mutation for cloning a repo
  const { 
    mutate: cloneRepo, 
    isPending: isCloning 
  } = useCloneGithubRepo();
  
  const handleCloneRepo = (repoName: string) => {
    cloneRepo({ repo_name: repoName });
  };
  
  if (isLoadingRepos) {
    return <div className="p-4">Loading repositories...</div>;
  }
  
  if (reposError) {
    return <div className="p-4 text-red-500">Error loading repositories</div>;
  }
  
  return (
    <div className="p-4">
      <h2 className="text-xl font-bold mb-4">Repositories</h2>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {repos?.map((repo) => (
          <div 
            key={repo.id} 
            className="border rounded-lg p-4 cursor-pointer hover:bg-gray-50"
            onClick={() => setSelectedRepoId(String(repo.id))}
          >
            <h3 className="font-semibold">{repo.name}</h3>
            <p className="text-sm text-gray-600">{repo.description}</p>
            <div className="mt-2 flex justify-between items-center">
              <span className="text-xs text-gray-500">
                Updated: {new Date(repo.updated_at).toLocaleDateString()}
              </span>
              <button
                className="bg-blue-500 text-white px-3 py-1 rounded text-sm"
                onClick={(e) => {
                  e.stopPropagation();
                  handleCloneRepo(repo.name);
                }}
                disabled={isCloning}
              >
                {isCloning ? 'Cloning...' : 'Clone'}
              </button>
            </div>
          </div>
        ))}
        
        {repos?.length === 0 && (
          <div className="col-span-full text-center py-8 text-gray-500">
            No repositories found
          </div>
        )}
      </div>
      
      {selectedRepoId && (
        <div className="mt-8">
          <h3 className="text-lg font-semibold mb-2">Tracking Events</h3>
          {isLoadingEvents ? (
            <div>Loading events...</div>
          ) : (
            <div className="border rounded-lg divide-y">
              {events?.map((event) => (
                <div key={event.id} className="p-3">
                  <div className="font-medium">{event.event_name}</div>
                  <div className="text-sm text-gray-600 mt-1">{event.context}</div>
                  <div className="flex gap-2 mt-2">
                    {event.tags.map((tag) => (
                      <span 
                        key={tag} 
                        className="bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                  <div className="text-xs text-gray-500 mt-2">
                    {event.file_path}:{event.line_number}
                  </div>
                </div>
              ))}
              
              {events?.length === 0 && (
                <div className="p-4 text-center text-gray-500">
                  No tracking events found for this repository
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default RepoList; 