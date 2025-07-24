from db_models import Plan, PlanRepo, Profile, Repo, UserEvent


def test_create_repo(db_session):
    repo = Repo(name="test", url="https://github.com/test/test")
    db_session.add(repo)
    db_session.commit()

    repo = db_session.query(Repo).first()
    assert repo.name == "test"
    assert repo.url == "https://github.com/test/test"


def test_create_plan(db_session):
    plan = Plan(name="test", description="test")
    db_session.add(plan)
    db_session.commit()

    plan = db_session.query(Plan).first()
    assert plan.name == "test"
    assert plan.description == "test"


def test_create_plan_repo(db_session):
    plan = Plan(name="test", description="test")
    repo = Repo(name="test", url="https://github.com/test/test")
    plan_repo = PlanRepo(plan=plan, repo=repo)
    db_session.add(plan_repo)
    db_session.commit()

    plan_repo = db_session.query(PlanRepo).first()
    assert plan_repo.plan.name == "test"
    assert plan_repo.repo.name == "test"


def test_create_plan_with_repo(db_session):
    plan = Plan(name="test", description="test")
    repo = Repo(name="test", url="https://github.com/test/test")
    plan.repos.append(repo)
    db_session.add(plan)
    db_session.commit()

    plan = db_session.query(Plan).first()
    assert plan.name == "test"
    assert plan.description == "test"
    assert len(plan.repos) == 1


def test_create_repo_with_plan(db_session):
    plan = Plan(name="test", description="test")
    repo = Repo(name="test", url="https://github.com/test/test")
    repo.plans.append(plan)
    db_session.add(repo)
    db_session.commit()

    repo = db_session.query(Repo).first()
    assert repo.name == "test"
    assert repo.url == "https://github.com/test/test"
    assert len(repo.plans) == 1


def test_create_plan_with_multiple_repos(db_session):
    plan = Plan(name="test", description="test")
    repo1 = Repo(name="test1", url="https://github.com/test/test1")
    repo2 = Repo(name="test2", url="https://github.com/test/test2")
    repo3 = Repo(name="test3", url="https://github.com/test/test3")

    plan.repos.append(repo1)
    plan.repos.append(repo2)
    plan.repos.append(repo3)

    db_session.add(plan)
    db_session.commit()

    plan = db_session.query(Plan).first()
    assert plan.name == "test"
    assert plan.description == "test"
    assert len(plan.repos) == 3


def test_create_user_event(db_session):
    user_event = UserEvent(
        event_name="test", context="test", tags="test", file_path="test", line_number=1
    )
    db_session.add(user_event)
    db_session.commit()

    user_event = db_session.query(UserEvent).first()
    assert user_event.event_name == "test"
    assert user_event.context == "test"
    assert user_event.tags == "test"
    assert user_event.file_path == "test"
    assert user_event.line_number == 1


def test_create_user_event_with_repo(db_session):
    repo = Repo(name="test", url="https://github.com/test/test")
    user_event = UserEvent(
        event_name="test",
        context="test",
        tags="test",
        file_path="test",
        line_number=1,
        repo=repo,
    )
    db_session.add(user_event)
    db_session.commit()

    user_event = db_session.query(UserEvent).first()
    assert user_event.event_name == "test"
    assert user_event.context == "test"
    assert user_event.repo.name == "test"
    assert user_event.repo.url == "https://github.com/test/test"


def test_create_user_event_with_multiple_repo_should_fail(db_session):
    repo1 = Repo(name="test1", url="https://github.com/test/test1")
    repo2 = Repo(name="test2", url="https://github.com/test/test2")
    user_event = UserEvent(
        event_name="test", context="test", tags="test", file_path="test", line_number=1
    )
    user_event.repo = repo1
    db_session.add(user_event)
    db_session.commit()

    assert user_event.repo.name == "test1"

    user_event = UserEvent(
        event_name="test", context="test", tags="test", file_path="test", line_number=1
    )
    user_event.repo = repo2
    db_session.add(user_event)
    db_session.commit()

    assert user_event.repo.name == "test2"
    assert user_event.repo.url == "https://github.com/test/test2"
    assert user_event.repo.name != "test1"


def test_create_user_event_wiht_multiple_plans(db_session):
    plan1 = Plan(name="test1", description="test1")
    plan2 = Plan(name="test2", description="test2")
    repo = Repo(name="test", url="https://github.com/test/test")
    user_event = UserEvent(
        event_name="test",
        context="test",
        tags="test",
        file_path="test",
        line_number=1,
        repo=repo,
    )

    plan1.repos.append(repo)
    plan2.repos.append(repo)

    db_session.add(plan1)
    db_session.add(plan2)
    db_session.add(user_event)
    db_session.commit()

    user_event = db_session.query(UserEvent).first()
    assert user_event.event_name == "test"
    assert user_event.context == "test"
    assert user_event.repo.name == "test"
    assert len(user_event.repo.plans) == 2


def test_delete_repo_with_user_event(db_session):
    repo = Repo(name="test", url="https://github.com/test/test")
    user_event = UserEvent(
        event_name="test",
        context="test",
        tags="test",
        file_path="test",
        line_number=1,
        repo=repo,
    )
    user_event2 = UserEvent(
        event_name="test2",
        context="test2",
        tags="test2",
        file_path="test2",
        line_number=2,
        repo=repo,
    )
    db_session.add(user_event)
    db_session.add(user_event2)
    db_session.add(repo)
    db_session.commit()

    db_session.delete(repo)
    db_session.commit()

    assert db_session.query(UserEvent).count() == 0


def test_create_profile(db_session):
    profile = Profile(name="test", avatar_url="https://example.com/avatar.png")
    db_session.add(profile)
    db_session.commit()

    profile = db_session.query(Profile).first()
    assert profile.name == "test"
    assert profile.avatar_url == "https://example.com/avatar.png"
