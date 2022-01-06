from gogettr import PublicClient
client = PublicClient()
posts = client.user_activity(username="mattgaetz", max=20, type="posts")
listOfPosts = [post for post in posts]
listOfPosts.reverse()
