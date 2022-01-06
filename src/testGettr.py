from gogettr import PublicClient

def getPosts(handle, amount):
    client = PublicClient()
    posts = client.user_activity(username=handle, max=amount, type="posts")
    listOfPosts = [post for post in posts]
    listOfPosts.reverse()
    return listOfPosts

massiePosts = getPosts("massieofficial", 1)
post = massiePosts[0]
print(post.get("action", "Nope!"))
print(post.get("uid", "Nope!"))

donaldsPosts = getPosts("repdonaldspress", 1)
post = donaldsPosts[0]
print(post.get("action", "Nope!"))
print(post.get("uid", "Nope!"))

#for key in post.keys():
#    print("{} = {}\n".format(key, post[key]))

#post["action"] = shares_pst
#post["uid"] = mtg4america

#post["action"] = pub_pst
#post["uid"] = repdonaldspress
