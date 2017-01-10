import os
import sys
import getpass
import pickle
import twitter
import atexit
from Crypto.Cipher import Blowfish
from passlib.context import CryptContext

CHAR_LIMIT = 140
SECRET_HOME = os.path.expanduser("~/.funnynotnever/")
SECRET_FILE = ".secrets"
CREDENTIAL_TAGS = ['consumer_key', 'consumer_secret', 'access_token_key', 'access_token_secret']

password_context = CryptContext(schemes=["bcrypt"], all__vary_rounds = 0.1)


@atexit.register
def exitDecorator():
    print("Exiting!")


def gatherCredentials():
    credentials = {CREDENTIAL_TAGS[0]: raw_input("Consumer Key: "),
        CREDENTIAL_TAGS[1]: raw_input("Consumer Secret: "),
        CREDENTIAL_TAGS[2]: raw_input("Access Token Key: "),
        CREDENTIAL_TAGS[3]: raw_input("Access Token Secret: ")}
    return credentials


def processSecretsFile(secrets_file):
    encrypted_credentials = pickle.Unpickler(secrets_file).load()
    cryptokey = getpass.getpass("Enter password for secrets file: ")
    if not password_context.verify(cryptokey, encrypted_credentials["pw"]):
        print("Incorrect password.")
        sys.exit()
    else:
        cipher = Blowfish.new(cryptokey)
        unencrypted_credentials = {key: cipher.decrypt(encrypted_credentials[key]).strip() for key in CREDENTIAL_TAGS}
    return unencrypted_credentials


def generateSecretsFile(credentials, file_and_path):
    cryptokey = getpass.getpass("Choose a password for your secrets file: ")
    cipher = Blowfish.new(cryptokey)
    encrypted_credentials = {}
    encrypted_credentials["pw"] = password_context.encrypt(cryptokey)
    for key in CREDENTIAL_TAGS:
        encrypted_credentials[key] = cipher.encrypt(credentials[key].rjust(512))
    try:
        os.mkdir(SECRET_HOME)
    except OSError: # OSError on os.mkdir means the directory already exists, so it's safe to ignore in this instance.
        pass
    with open(file_and_path, 'w') as secrets_file:
        pickle.Pickler(secrets_file).dump(encrypted_credentials)
    return credentials


def promptForMessage():
    message = raw_input("Message: ")
    message_length = len(message)
    if message_length > CHAR_LIMIT:
        original_message = message
        message = message[:CHAR_LIMIT]
        print("\n***Message \"{}\" over the 140 character limit.***\n\nTruncated to:\n\"{}\"\n\n"
            .format(original_message, message))
    elif message_length == 0:
        sys.exit()
    return message


def promptForTweetApproval(message, twitter_creds):
    prompt = raw_input("\"{}\" will be posted by {}.\n[y/N]: "
        .format(message, twitter_creds.AsDict()["name"]))
    if prompt.lower() == "y":
        return True
    else:
        return False


def promptForTweet(twit_creds):
    while True:
        message = promptForMessage()
        approval = promptForTweetApproval(message, twit_creds)
        if approval == True:
            return message


def logIn():
    file_and_path = SECRET_HOME + SECRET_FILE

    #check if the secrets file and directory exist
    #if they do, prompt user for password, use that password to decrypt credentials
    #if they do not, obtain credentials from the user and store them using a password
    #
    #Returns an unencrypted object that represents the (unencrypted) twitter credentials to be passed to the twitter API

    if os.path.isfile(file_and_path):
        with open(file_and_path, 'r') as secrets_file:
            credentials = processSecretsFile(secrets_file)
            return credentials
    else:
        credentials = gatherCredentials()
        generateSecretsFile(credentials, file_and_path)
        return credentials


def initTwitterAPI(credentials):
    api = twitter.Api(**credentials)
    return api


def main():
    credentials = logIn()
    api = initTwitterAPI(credentials)
    twitcreds = api.VerifyCredentials()
    message = promptForTweet(twitcreds)
    status = api.PostUpdate(message)
    sys.exit()


if __name__ == "__main__":
    main()
