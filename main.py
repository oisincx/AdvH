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
        "CREATE TABLE IF NOT EXISTS Publications(authorString VARCHAR(255) NOT NULL, publishYear YEAR NOT NULL, sourceTitle VARCHAR(255) NOT NULL, journalString VARCHAR(100) NOT NULL, doiURL VARCHAR(70) NOT NULL PRIMARY KEY, pathToPDF VARCHAR(255));",
        "CREATE TABLE IF NOT EXISTS Administrators(username VARCHAR(255) NOT NULL PRIMARY KEY, password VARCHAR(256) NOT NULL);"
        ]
    for query in queries:
        try:
            cursor.execute(query)
        except:
            print("Failed to create tables")
            quit()
    conn.commit()


class Publication:
    def __init__(self, authorString, publishYear, sourceTitle, journalString, doiURL, pathToPDF):
        self._authorString = authorString
        self._publishYear = publishYear
        self._sourceTitle = sourceTitle
        self._journalString = journalString
        self._doiURL = doiURL
        self._pathToPDF = pathToPDF
    def generateCitation(self):
        return f"{self.getAuthorString()} ({self.getPublishYear()}). {self.getSourceTitle()}. {self.getJournalString()}. {self.getDoiURL()}"
    #Getters
    def getAuthorString(self):
        return self._authorString
    def getPublishYear(self):
        return int(self._publishYear)
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
    def setPublishYear(self, publishYear):
        self._publishYear = publishYear
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

        while position > 0 and publications[position - 1].getPublishYear() < current.getPublishYear():
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
        if publications[middle].getPublishYear() == query:
            found = True
        elif publications[middle].getPublishYear() > query:
            start = middle + 1
        else:
            end = middle -1
    return found, middle


def validateCredentials(admin, conn, cursor):
    try:
        cursor.execute(f"SELECT * FROM Administrators WHERE username = '{admin.getUsername()}' COLLATE NOCASE AND password = '{hash(admin.getPassword(), passwordSalt)}';")
        return not (len(cursor.fetchall()) == 0)
    except:
        print("Database lookup failed!")
        return False


def validateInput(dataType, value):
    dataType = str(dataType).lower()

    match dataType:
        case 'authorstring':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("The authorString cannot be longer than 255 characters or empty!")
            return value

        case 'publishyear':
            if len(value) > 4 or len(value) <= 0 or not value.isdigit():
                raise ValueError("The publishYear cannot be longer than 4 characters, non-numeric or empty!")
            return int(value)

        case 'sourcetitle':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("The publication title cannot be longer than 255 characters or empty!")
            return value

        case 'journalstring':
            if len(value) > 100 or len(value) <= 0:
                raise ValueError("journalString cannot be longer than 100 characters or empty!")
            return value

        case 'doiurl':
            value = value.lower()
            if not value.startswith("https://") or len(value) > 70 or len(value) <= 0:
                raise ValueError("DOI must start with 'https://' and be <= 70 characters and cannot be empty")
            return value

        case 'pdf':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("PDF Path cannot be longer than 255 characters or empty!")
            return value

        case 'username':
            if len(value) > 255 or len(value) <= 0:
                raise ValueError("Your username cannot be longer than 255 characters or empty!")
            return value

        case 'password':
            if len(value) > 256 or len(value) <= 0:
                raise ValueError("Your password cannot be longer than 256 characters or empty!")
            return value


def getValidatedCLIInput(dataType, prompt):
    while True:
        user_input = input(prompt)
        try:
            return validateInput(dataType, user_input)
        except ValueError as e:
            print(e)


def newAdminOnboard(conn, cursor):
    print("-----------------------")
    print("Administrator Management")
    username = getValidatedCLIInput('username', "What will the new admin's username be?: ")
    password = getValidatedCLIInput('password', "What will the new admin's password be?: ")
    admin = Administrator(username, password)
    if createAdmin(conn, cursor, admin):
        print(f"Succesfully created admin with username {username}!")
    else:
        print("Failed to create admin!")


def publicationWizard(): # Ideally this should be able to parse pre made APA citations but like whatevs
    print("-----------------------")
    print("Publication Wizard!")
    authorString = getValidatedCLIInput("authorstring", "Please enter the APA formatted author list: ")
    publishYear = getValidatedCLIInput("publishYear", "Please enter the year this publication was published: ")
    sourceTitle = getValidatedCLIInput("sourcetitle", "Please enter the title of the publication: ")
    journalString = getValidatedCLIInput("journalstring", "Please enter the name of the Journal: ")
    doiURL = getValidatedCLIInput("doiurl", "Please enter the DOI of the publication, including https:// : ")
    PDF = getValidatedCLIInput("pdf", "Please enter the path to the PDF relative to the current working directory: ")
    publication = Publication(authorString, publishYear, sourceTitle, journalString, doiURL, PDF)
    return publication


def insertPublication(conn, cursor, publication):
    values = f'"{publication.getAuthorString()}", "{publication.getPublishYear()}", "{publication.getSourceTitle()}", "{publication.getJournalString()}", "{publication.getDoiURL()}", "{publication.getPathToPDF()}"'
    query = f"INSERT INTO Publications VALUES ({values});"
    cursor.execute(query)
    conn.commit()


def deletePublicationWizard():
    doi = getValidatedCLIInput('doiurl', "Please enter the full DOI URL of the publication you want to delete.")
    return doi


def deletePublication(conn, cursor, doi):
    sql = f"DELETE FROM Publications WHERE doiURL = '{doi}';"
    try:
        cursor.execute(sql)
    except:
        print("Failed to execute query!")
        return False
    conn.commit()
    return cursor.rowcount


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
            doi = deletePublicationWizard()
            result = deletePublication(conn, cursor, doi)
            if result > 0:
                print(f"Deleted {str(cursor.rowcount)} publications according to this query, if > 1 then duplicate entries existed.")
            else:
                print("No publications matching that DOI were found!")
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


def searchDatabase(column, query):
    if column == 'publishYear': # Therefore with binary search
        sortDatabase(conn, cursor) # Makes sure the database is sorted before doing binary search
        print("Binary search started")
        publications = loadPublications(conn, cursor, "SELECT * FROM Publications;")
        results = []
        found, resulti = binarySearch(publications, query)
        while found:
            if found == True:
                results.append(publications[resulti])
                publications.pop(resulti)
            found, resulti = binarySearch(publications, query)
        if len(results) <= 0: return False
        else: return results
    sql = f'SELECT * FROM Publications WHERE {column} = "{query}" COLLATE NOCASE;'
    results = loadPublications(conn, cursor, sql)
    if len(results) <= 0: return False
    else: return results


def databaseSearchWizard():
    print("-----------------------")
    print("Which column would you like to search the database by?")
    print("1. authorString")
    print("2. publishYear (Fast Search!)")
    print("3. sourceTitle")
    print("4. Journal")
    print("5. DOI URL")
    choice = input("\n#")
    print("Please enter your search term.")
    column = ""
    match choice:
        case '1':
            column = 'authorString'
            query = getValidatedCLIInput(column, "\n#")
        case '2':
            column = 'publishYear'
            query = getValidatedCLIInput(column, "\n#")
        case '3':
            column = 'sourceTitle'
            query = getValidatedCLIInput(column, "\n#")
        case '4':
            column = 'journalString'
            query = getValidatedCLIInput(column, "\n#")
        case '5':
            column = 'doiURL'
            query = getValidatedCLIInput(column, "\n#")
        case _:
            print("Please enter a valid column!")
            databaseSearchWizard()
    results = searchDatabase(column, query)
    if results:
        outputPublications(results)
    else:
        print("No publications matching your query were found!")


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
            username = getValidatedCLIInput('username', "What is your username?: ")
            password = getValidatedCLIInput('password', "What is your password?: ")
            potentialAdmin = Administrator(username, password)
            if validateCredentials(potentialAdmin, conn, cursor):
                loggedIn = Administrator(username, password)
                adminPanel(loggedIn)
            else:
                print("Incorrect credentials!")
            main()
        case '3':
            databaseSearchWizard()
            main()
        case '4':
            print("Quitting...")
            quit()
        case _:
            print("Invalid input!")
            main()


# Kick everything off!
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
