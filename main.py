import sqlite3, hashlib, os
passwordSalt = '5lo' # Arbritary but hopefully vaguely unqiue! Means pre computed hases are kaput

def connectDB(database):
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        return conn, cursor
    except:
        print("Failed to connect to the database!")
        return False

def makeTables(conn, cursor):
    queries = [
        "CREATE TABLE IF NOT EXISTS Publications(authorString VARCHAR(255) NOT NULL, publishDate YEAR NOT NULL, sourceTitle VARCHAR(255) NOT NULL, journalString VARCHAR(100) NOT NULL, doiURL VARCHAR(70) NOT NULL PRIMARY KEY, pathToPDF VARCHAR(255));",
        "CREATE TABLE IF NOT EXISTS Administrators(username VARCHAR(255) NOT NULL PRIMARY KEY, password VARCHAR(64) NOT NULL);"
        ]
    for query in queries:
        try:
            cursor.execute(query)
        except:
            print("Failed to create tables")
            quit()
    conn.commit()



class Publication:
    def __init__(self, authorString, publishDate, sourceTitle, journalString, doiURL, pathToPDF):
        self._authorString = authorString
        self._publishDate = publishDate
        self._sourceTitle = sourceTitle
        self._journalString = journalString
        self._doiURL = doiURL
        self._pathToPDF = pathToPDF
    def generateCitation(self):
        return f"{self.getAuthorString()} ({self.getPublishDate()}) {self.getSourceTitle()}. {self.getJournalString()}, {self.getDoiURL()}"
    #Getters
    def getAuthorString(self):
        return self._authorString
    def getPublishDate(self):
        return int(self._publishDate)
    def getSourceTitle(self):
        return self._sourceTitle
    def getJournalString(self):
        return self._journalString
    def getDoiURL(self):
        return self._doiURL
    def getPathToPDF(self):
        return self._pathToPDF
    #Setters
    def setAuthorString(self, authorString):
        self._authorString = authorString
        return True
    def setPublishDate(self, publishDate):
        self._publishDate = publishDate
    def setSourceTitle(self, sourceTitle):
        self._sourceTitle = sourceTitle
    def setPublisherString(self, publisherString):
        self._publisherString = publisherString
    def setDoiURL(self, doiURL):
        self._doiURL = doiURL
    def setPathToPDF(self, pathToPDF):
        self._pathToPDF = pathToPDF


class Administrator:
    def __init__(self, username, password):
        self._username = username.lower()
        self._password = password
    def getUsername(self):
        return self._username
    def getPassword(self):
        return self._password
    def setUsername(self, username):
        self._username = username.lower()
    def setPassword(self, password):
        self._password = password


def hash(password, salt):
    return hashlib.sha256((password + salt).encode()).hexdigest()

def createAdmin(conn, cursor, admin):
    try:
        cursor.execute(f"INSERT INTO Administrators VALUES ( '{admin.getUsername()}' , '{ hash(admin.getPassword(), passwordSalt) }');")
        conn.commit()
    except Exception as e:
        print("Database query failed!", e)
        return False
    return True

def dateInsertionSort(publications): # Descending order
    for index in range(1, len(publications)):
        current = publications[index]
        position = index

        while position > 0 and publications[position - 1].getPublishDate() < current.getPublishDate():
            publications[position] = publications[position - 1]
            position -= 1

        publications[position] = current

    return publications



def binarySearch(publications, query): # Descending order
    found = False
    middle = -1
    start = 0
    end = len(publications)-1
    while (found == False) and (start <= end):
        middle = ((start+end) // 2)
        if publications[middle].getPublishDate() == query:
            found = True
        elif publications[middle].getPublishDate() > query:
            start = middle + 1
        else:
            end = middle -1
    return found, middle


def validateCredentials(username, password, conn, cursor):
    try:
        cursor.execute(f"SELECT * FROM Administrators WHERE username = '{username}' COLLATE NOCASE AND password = '{hash(password, passwordSalt)}';")
        return not (len(cursor.fetchall()) == 0)
    except:
        print("Database lookup failed!")
        return False

def newAdminOnboard(conn, cursor):
    print("-----------------------")
    print("Administrator Management")
    username = input("What will the new admin's username be?: ")
    password = input("What will the new admin's password be?: ")
    admin = Administrator(username, password)
    if createAdmin(conn, cursor, admin):
        print(f"Succesfully created admin with username {username}!")
    else:
        print("Failed to create admin!")


def publicationWizard(): # Ideally this should be able to parse pre made APA citations but like whatevs
    print("-----------------------") 
    print("Publication Wizard!")
    authorString = input("Please enter the APA formatted author list: ")
    publishDate = input("Please enter the year this publication was published: ")
    sourceTitle = input("Please enter the title of the publication: ")
    journalString = input("Please enter the name of the Journal: ")
    doiURL = input("Please enter the DOI of the publication, including https:// : ")
    PDF = input("Please enter the path to the PDF relative to the current working directory: ")
    publication = Publication(authorString, publishDate, sourceTitle, journalString, doiURL, PDF)
    return publication

def insertPublication(conn, cursor, publication):
    values = f'"{publication.getAuthorString()}", "{publication.getPublishDate()}", "{publication.getSourceTitle()}", "{publication.getJournalString()}", "{publication.getDoiURL()}", "{publication.getPathToPDF()}"'
    query = f"INSERT INTO Publications VALUES ({values});"
    cursor.execute(query)
    conn.commit()

def adminPanel(admin):
    print(f"Hello, {admin.getUsername()}")
    print("-----------------------")
    print("Admin Panel")
    print("1. Add new publication")
    print("2. Delete publication")
    print("3. Add new Administrator")
    print("4. Exit admin panel")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            print("Adding publication")
            pub = publicationWizard()
            insertPublication(conn,cursor,pub)
            adminPanel(admin)
        case '2':
            print("Please enter the full DOI URL of the publication you want to delete.")
            doi = input("\n#")
            sql = f"DELETE FROM Publications WHERE doiURL = '{doi}';"
            try:
                cursor.execute(sql)
            except:
                print("Failed to execute query!")
                adminPanel(admin)
            if cursor.rowcount > 0:
                print(f"Deleted {str(cursor.rowcount)} publications according to this query, if > 1 then duplicate entries existed.")
            else:
                print("No publications matching that DOI were found!")
            conn.commit()
            adminPanel(admin)
        case '3':
            newAdminOnboard(conn, cursor)
            adminPanel(admin)
        case '4':
            print("Exiting admin panel..")
        case _:
            print("Invalid input!")
            adminPanel(admin)


def loadData(path, conn, cursor): # This is just a helper function to help load in mock data for testing
    f = open(path, 'r', encoding='utf-8')
    data = f.readlines()
    #data.pop(0) # pop the definition line because my parser assumes a specific order
    for row in data:
        row = row.rstrip('\n')
        columns = row.split('|')
        values = ""
        for column in columns:
            values += f'"{column}"' + ','
        values = values[:-1] # pop that last comma
        query = f"INSERT INTO Publications VALUES ({values});"
        
        print(query)
        cursor.execute(query)
        conn.commit()
    f.close()

def loadPublications(conn, cursor, query):
    publications = []
    try:
        cursor.execute(query)
        data = cursor.fetchall()
        for row in data:
            entry = Publication(row[0], row[1], row[2], row[3], row[4], row[5])
            publications.append(entry)
    except:
        print("Failed to perform database lookup!")
    return publications

def insertPublications(conn, cursor, publications):
    for publication in publications:
        insertPublication(conn, cursor, publication)

def dropPublications(conn, cursor):
    cursor.execute("DROP TABLE Publications;")
    conn.commit()

def outputPublications(publications):
    print("-----------------------")
    for index, publication in enumerate(publications): # Fancy python for each loop that lets me keep an index
        print(f"{index+1}. {publication.generateCitation()}")
        print("-----------------------")

def sortDatabase(conn, cursor):
    publications = loadPublications(conn, cursor, "SELECT * FROM Publications;")
    publications = dateInsertionSort(publications)
    print("DO NOT TERMINATE PROGRAM")
    # Gets a bit dangerous here as the only copy of the database is in memory
    dropPublications(conn, cursor)
    makeTables(conn, cursor)
    insertPublications(conn, cursor, publications)

def databaseSearch():
    sortDatabase(conn, cursor)
    print("-----------------------")
    print("Which column would you like to search the database by?")
    print("1. authorString")
    print("2. publishYear (Fast Search!)")
    print("3. sourceTitle")
    print("4. Journal")
    print("5. DOI URL")
    choice = input("\n#")
    print("Please enter your search term.")
    query = input("\n#")
    column = ""
    match choice:
        case '1':
            column = 'authorString'
        case '2':
            try:
                query = int(query)
            except:
                print("Invalid search term!")
                databaseSearch()
            publications = loadPublications(conn, cursor, "SELECT * FROM Publications;")
            results = []
            found, resulti = binarySearch(publications, query)
            while found:
                if found == True:
                    results.append(publications[resulti])
                    publications.pop(resulti)
                found, resulti = binarySearch(publications, query)
            if (len(results) > 0):
                outputPublications(results)
            else:
                print("No publications matching that year were found!")
            return
        case '3':
            column = 'sourceTitle' 
        case '4':
            column = 'journalString'
        case '5':
            column = 'doiURL'
    sql = f'SELECT * FROM Publications WHERE {column} = "{query}" COLLATE NOCASE;'
    results = loadPublications(conn, cursor, sql)
    if len(results) > 0:
        outputPublications(results)
    else:
        print("No publications matchin your query were found!")

def main():
    print("-----------------------")
    print("Academic Database")
    print("1. View database sorted by date published descending")
    print("2. Login as an Admin")
    print("3. Search the database")
    print("4. Exit the program")
    print("-----------------------")
    choice = input("\n#")
    match choice:
        case '1':
            sortDatabase(conn, cursor)
            print("Sorted database")
            publications = loadPublications(conn, cursor, "SELECT * FROM Publications;")
            outputPublications(publications)
            main()
        case '2':
            username = input("What is your username?: ")
            password = input("What is your password?: ")
            if validateCredentials(username, password, conn, cursor):
                loggedIn = Administrator(username, password)
                adminPanel(loggedIn)
            else:
                print("Incorrect credentials!")
            main()
        case '3':
            databaseSearch()
            main()
        case '4':
            print("Quitting...")
            quit()
        case _:
            print("Invalid input!")
            main()


database = 'database.db'
firstRun = not (os.path.exists(database))
value = connectDB(database)
if not (value == False):
    conn, cursor = value
else:
    print("Failed to connect to the database!")
    quit()
makeTables(conn, cursor)
if firstRun:
    print("It appears this is your first time running the program, Please make an Administrator account!")
    newAdminOnboard(conn, cursor)
#loadData('2025.csv', conn, cursor)
sortDatabase(conn, cursor)
main()
