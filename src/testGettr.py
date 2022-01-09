from gogettr import PublicClient

def getPosts(handle, amount):
    client = PublicClient()
    posts = client.user_activity(username=handle, max=amount, type="posts")
    listOfPosts = [post for post in posts]
    listOfPosts.reverse()
    return listOfPosts

def getComments(handle, amount):
    client = PublicClient()
    comments = client.user_activity(username=handle, max=amount, type="comments")
    listOfComments = [comment for comment in comments]
    listOfComments.reverse()
    return listOfComments

def getSinglePost(id_str):
    client = PublicClient()
    response = client.all(first=id_str, last=id_str)
    listOfPosts = [post for post in response]
    return listOfPosts[0]

def getSingleComment(id_str):
    client = PublicClient()
    response = client.all(first=id_str, last=id_str, type="comments")
    listOfPosts = [post for post in response]
    return listOfPosts[0]

def printKeyValues(post):
    for key in post.keys():
        print("{} = {}\n".format(key, post[key]))

##posts = getPosts("mattgaetz", 20)
##post = posts[0]
##print(post.get("action", "Nope!"))
##print(post.get("uid", "Nope!"))

comments = getComments("mtg4america", 20)
comment = comments[0]

#post["action"] = shares_pst
#post["uid"] = mtg4america
#post["action"] = pub_pst
#post["uid"] = repdonaldspress

# https://www.gettr.com/post/pmvyup028a
#post = getSinglePost("pmvyup028a")
#rpstIds = ['pmw66we12b']
#rusrIds = ['mariabartiromo']

#post = getSinglePost("pmgr4v7a61")
#comment = getSingleComment("cfs2965cb2")
