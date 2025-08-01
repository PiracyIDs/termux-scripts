#!/data/data/com.termux/files/usr/bin/python

# Telegram Patcher script in python
# @author: Abhi (@AbhiTheModder)

# Patch credits:  @Zylern_OP, @rezaAa1177, @AbhiTheModder and Nekogram


import argparse
import os
import re
import sys

RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"  # No Color

HOOK_SMALI = """
.class public Lorg/telegram/abhi/Hook;
.super Ljava/lang/Object;
.source "SourceFile"


# static fields
.field public static candelMessages:Z


# direct methods
.method public constructor <init>()V
    .registers 1

    invoke-direct {p0}, Ljava/lang/Object;-><init>()V

    return-void
.end method

.method public static hook()V
    .registers 1

    const/4 v0, 0x1

    .line 17
    invoke-static {v0}, Lorg/telegram/abhi/Hook;->setCanDelMessages(Z)V

    return-void
.end method

.method public static setCanDelMessages(Z)V
    .registers 4

    sput-boolean p0, Lorg/telegram/abhi/Hook;->candelMessages:Z

    sget-object v0, Lorg/telegram/messenger/ApplicationLoader;->applicationContext:Landroid/content/Context;

    const-string v1, "mainconfig"

    const/4 v2, 0x0

    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    const-string v1, "candelMessages"

    invoke-interface {v0, v1, p0}, Landroid/content/SharedPreferences$Editor;->putBoolean(Ljava/lang/String;Z)Landroid/content/SharedPreferences$Editor;

    move-result-object v0

    invoke-interface {v0}, Landroid/content/SharedPreferences$Editor;->apply()V

    return-void
.end method

.method public static unhook()V
    .registers 1

    .line 23
    sget-boolean v0, Lorg/telegram/abhi/Hook;->candelMessages:Z

    if-eqz v0, :cond_8

    const/4 v0, 0x0

    .line 24
    invoke-static {v0}, Lorg/telegram/abhi/Hook;->setCanDelMessages(Z)V

    :cond_8
    return-void
.end method
"""


class NoMethodFoundError(Exception):
    """Exception raised when the method is not found in the file."""

    pass


def find_smali_file(root_directory, target_file):
    """Recursively search for the target file within the root directory."""
    for dirpath, _, filenames in os.walk(root_directory):
        if target_file in filenames:
            return os.path.join(dirpath, target_file)
    return None


def find_smali_file_by_method(root_directory, method_name):
    """Recursively search for the method in any smali file within the root directory."""
    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith(".smali"):
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r") as file:
                    file_content = file.read()
                    if method_name in file_content:
                        return file_path
    return None


def modify_method(file_path, method_name, new_method_code):
    """Modify the method in the smali file."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    in_method = False
    new_lines = []
    method_found = False

    for line in lines:
        if f".method {method_name}" in line:
            in_method = True
            method_found = True
            new_lines.extend(new_method_code)
            continue

        if in_method:
            if ".end method" in line:
                in_method = False
            continue

        new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        raise NoMethodFoundError(
            f"{YELLOW}WARN: {NC}Method {method_name} not found in the file."
        )


def modify_del_method(file_path, method_name, new_method_code):
    """Modify the method in the smali file."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    in_method = False
    in_annotation = False
    method_found = False
    annotation_end_index = -1
    new_lines = []

    for i, line in enumerate(lines):
        if f".method {method_name}" in line:
            in_method = True
            method_found = True
            new_lines.append(line)
            continue

        if in_method:
            if ".annotation" in line:
                in_annotation = True
            elif in_annotation and ".end annotation" in line:
                in_annotation = False
                annotation_end_index = i

            if (
                not in_annotation
                and annotation_end_index != -1
                and i > annotation_end_index
            ):
                new_lines.extend(new_method_code)
                annotation_end_index = -1

            new_lines.append(line)

            if ".end method" in line:
                in_method = False
        else:
            new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        raise NoMethodFoundError(
            f"{YELLOW}WARN: {NC}Method {method_name} not found in the file."
        )


def copy_method(file_path, original_method_name, new_method_name):
    """Copy the method in the smali file."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    in_method = False
    method_found = False
    method_lines = []

    for line in lines:
        if f".method {original_method_name}" in line:
            in_method = True
            method_found = True
            method_lines.append(line.replace(original_method_name, new_method_name))
            continue

        if in_method:
            method_lines.append(line)
            if ".end method" in line:
                in_method = False

    if method_found:
        with open(file_path, "a") as file:
            file.writelines(method_lines)
        print(
            f"{GREEN}INFO: {NC}Method {original_method_name} copied to {new_method_name} successfully."
        )
    else:
        print(f"{YELLOW}WARN: {NC}Method {original_method_name} not found in the file.")


def apply_regex(root_directory, search_pattern, replace_pattern, file_path=None):
    """Apply a regex search and replace patch across all smali files in the root directory or a specific file."""
    pattern = re.compile(search_pattern)

    if file_path:
        with open(file_path, "r") as file:
            file_content = file.read()

        new_content = pattern.sub(replace_pattern, file_content)

        if new_content != file_content:
            with open(file_path, "w") as file:
                file.write(new_content)
            print(f"{GREEN}INFO: {NC}Applied regex patch to {file_path}")
    else:
        for dirpath, _, filenames in os.walk(root_directory):
            for filename in filenames:
                if filename.endswith(".smali"):
                    file_path = os.path.join(dirpath, filename)
                    with open(file_path, "r") as file:
                        file_content = file.read()

                    new_content = pattern.sub(replace_pattern, file_content)

                    if new_content != file_content:
                        with open(file_path, "w") as file:
                            file.write(new_content)
                        print(f"{GREEN}INFO: {NC}Applied regex patch to {file_path}")


def apply_isRestrictedMessage(root_directory):
    """Access Banned Channels [Related]"""
    search_pattern = r"(iget-boolean\s([v|p]\d+)\, ([v|p]\d+)\, Lorg/telegram/.*isRestrictedMessage:Z)"
    replace_pattern = r"\1\nconst \2, 0x0"
    apply_regex(root_directory, search_pattern, replace_pattern)


def apply_enableSavingMedia(root_directory):
    """Enabling Saving Media Everywhere"""
    search_pattern = (
        r"(iget-boolean\s([v|p]\d+)\, ([v|p]\d+)\, Lorg/telegram/.*noforwards:Z)"
    )
    replace_pattern = r"\1\nconst \2, 0x0"
    apply_regex(root_directory, search_pattern, replace_pattern)


def apply_premiumLocked(root_directory):
    """make premiumLocked bool false."""
    search_pattern = (
        r"(iget-boolean\s([v|p]\d+)\, ([v|p]\d+)\, Lorg/telegram/.*premiumLocked:Z)"
    )
    replace_pattern = r"\1\nconst \2, 0x0"
    apply_regex(root_directory, search_pattern, replace_pattern)


def apply_EnableScreenshots(root_directory):
    """Enables Screenshots"""
    initial_search_pattern = r"Landroid/view/Window;->.*Flags"
    secondary_search_pattern = r"const/16 (.*), 0x2000"
    replace_pattern = r"const/16 \1, 0x0"

    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith(".smali"):
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r") as file:
                    file_content = file.read()

                initial_matches = re.findall(initial_search_pattern, file_content)

                if initial_matches:
                    new_content = file_content
                    for match in initial_matches:
                        new_content = re.sub(
                            secondary_search_pattern, replace_pattern, new_content
                        )

                    if new_content != file_content:
                        with open(file_path, "w") as file:
                            file.write(new_content)
                        print(
                            f"{GREEN}INFO: {NC}Applied windowFlags patch to {file_path}"
                        )


def apply_EnableScreenshots2(root_directory):
    """Enables Screenshots"""
    search_pattern1 = r"(sget-boolean\s([v|p]\d+).*SharedConfig;->allowScreenCapture:Z)"
    replace_pattern1 = r"\1\nconst \2, 0x1"

    search_pattern2 = r"(iget-boolean\s([v|p]\d+)\, ([v|p]\d+)\, Lorg/telegram/ui/.*allowScreenshots:Z)"
    replace_pattern2 = r"\1\nconst \2, 0x1"

    for dirpath, _, filenames in os.walk(root_directory):
        for filename in filenames:
            if filename.endswith(".smali"):
                file_path = os.path.join(dirpath, filename)
                with open(file_path, "r") as file:
                    file_content = file.read()

                new_content = re.sub(search_pattern1, replace_pattern1, file_content)

                new_content = re.sub(search_pattern2, replace_pattern2, new_content)

                if new_content != file_content:
                    with open(file_path, "w") as file:
                        file.write(new_content)
                    print(
                        f"{GREEN}INFO: {NC}Applied allowScreenCapture patch to {file_path}"
                    )


def apply_EnableScreenshots3(root_directory):
    """Enables Screenshots"""
    search_pattern = r"or-int/lit16\s+([vp]\d+),\s+([vp]\d+),\s+0x2000"
    replace_pattern = r"or-int/lit16 \1, \1, 0x0"

    secret_media_viewer_path = find_smali_file(
        root_directory, "SecretMediaViewer.smali"
    )
    if secret_media_viewer_path:
        apply_regex(
            root_directory, search_pattern, replace_pattern, secret_media_viewer_path
        )

    photo_viewer_path = find_smali_file(root_directory, "PhotoViewer.smali")
    if photo_viewer_path:
        apply_regex(root_directory, search_pattern, replace_pattern, photo_viewer_path)


def modify_isPremium(file_path):
    """Modify isPremium method to return true."""
    new_method_code = [
        ".method public isPremium()Z\n",
        "    .locals 1\n",
        "    const/4 v0, 0x1\n",
        "    return v0\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "public isPremium()Z", new_method_code)
    except NoMethodFoundError as e:
        print(e)


def modify_markMessagesAsDeleted(file_path):
    """Modify markMessagesAsDeleted methods"""
    smali_dir = os.path.dirname(file_path).split("/")[0:2]
    root_dir = os.path.dirname(file_path).split("/")[0]
    if "archive-info.json" in os.listdir(root_dir):
        smali_dir.append("classes")
    smali_dir = "/".join(smali_dir)
    new_dir = os.path.join(smali_dir, "org", "telegram", "abhi")
    if not os.path.exists(new_dir):
        os.makedirs(new_dir, exist_ok=True)
    hook_file = os.path.join(new_dir, "Hook.smali")
    with open(hook_file, "w") as file:
        file.write(HOOK_SMALI)

    search_pattern = r"sget\s([v|p]\d),\sLorg/telegram/messenger/R\$string;->ShowAds:I\n+\s+(invoke-static\s{\1},\sLorg/telegram/messenger/LocaleController;->getString\(I\)Ljava/lang/String;\n+\s+move-result-object\s\1|goto\s:goto_\d+)((\n.*)*?)invoke-virtual\s({.*}),\sLorg/telegram/ui/Cells/TextCell;->setTextAndCheck\(Ljava/lang/CharSequence;ZZ\)V"

    search_pattern2 = r"sget\s([v|p]\d),\sLorg/telegram/messenger/R\$string;->ShowAdsInfo:I\n+\s+(invoke-static\s{\1},\sLorg/telegram/messenger/LocaleController;->getString\(I\)Ljava/lang/String;\n+\s+move-result-object\s\1|goto\s:goto_\d+)"

    search_pattern3 = r"sget\s([v|p]\d),\sLorg/telegram/messenger/R\$string;->ShowAdsTitle:I\n+\s+(invoke-static\s{\1},\sLorg/telegram/messenger/LocaleController;->getString\(I\)Ljava/lang/String;\n+\s+move-result-object\s\1|goto\s:goto_\d+)"

    replace_pattern = r'const-string \1, "Do Not Delete Messages"\n\3\4\n    invoke-virtual \5, Lorg/telegram/ui/Cells/TextCell;->setTextAndCheck2(Ljava/lang/CharSequence;ZZ)V'
    replace_pattern2 = r'const-string \1, "After enabling or disabling the feature, ensure you revisit this page for the changes to take effect.\\nMod by Abhi"'
    replace_pattern3 = r'const-string \1, "Anti-Delete Messages"\n    invoke-virtual {v1, \1}, Lorg/telegram/ui/Cells/HeaderCell;->setText(Ljava/lang/CharSequence;)V\n    return-void'

    search_patterns = [search_pattern, search_pattern2, search_pattern3]
    replace_patterns = [replace_pattern, replace_pattern2, replace_pattern3]

    for i, s_p in enumerate(search_patterns):
        apply_regex(root_dir, s_p, replace_patterns[i])

    automate_modification(root_dir, "TextCell.smali", create_delcopy_method)

    automate_modification(root_dir, "LaunchActivity.smali", modify_del_oncreate_method)

    new_code_to_append = [
        "    sget-boolean v0, Lorg/telegram/abhi/Hook;->candelMessages:Z\n",
        "    if-eqz v0, :cond_7\n",
        "    const/4 p1, 0x0\n",
        "    return-object p1\n",
        "    :cond_7\n",
    ]
    new_code_to_append2 = [
        "    sget-boolean v0, Lorg/telegram/abhi/Hook;->candelMessages:Z\n",
        "    if-eqz v0, :cond_7\n",
        "    const/4 v1, 0x0\n",
        "    return-object v1\n",
        "    :cond_7\n",
    ]

    try:
        modify_del_method(
            file_path,
            "public markMessagesAsDeleted(JIZZ)Ljava/util/ArrayList;",
            new_code_to_append,
        )
    except NoMethodFoundError as e:
        print(e)

    try:
        modify_del_method(
            file_path,
            "public markMessagesAsDeleted(JLjava/util/ArrayList;ZZII)Ljava/util/ArrayList;",
            new_code_to_append2,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_del_oncreate_method(file_path):
    method_name = "protected onCreate(Landroid/os/Bundle;)V"
    method_name2 = "public onCreate(Landroid/os/Bundle;)V"  # For plus
    with open(file_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    in_method = False
    method_found = False
    cond_label_pattern = re.compile(r":cond_\d")
    new_codes = [
        "    sget-object v0, Lorg/telegram/messenger/ApplicationLoader;->applicationContext:Landroid/content/Context;\n",
        '    const-string v1, "mainconfig"\n',
        "    const/4 v2, 0x0\n",
        "    invoke-virtual {v0, v1, v2}, Landroid/content/Context;->getSharedPreferences(Ljava/lang/String;I)Landroid/content/SharedPreferences;\n",
        "    move-result-object v0\n",
        '    const-string v1, "candelMessages"\n',
        "    const/4 v2, 0x0\n",
        "    invoke-interface {v0, v1, v2}, Landroid/content/SharedPreferences;->getBoolean(Ljava/lang/String;Z)Z\n",
        "    move-result v0\n",
        "    sput-boolean v0, Lorg/telegram/abhi/Hook;->candelMessages:Z\n",
    ]

    for line in lines:
        if f".method {method_name}" or f".method {method_name2}" in line:
            in_method = True
            method_found = True
            new_lines.append(line)
            continue

        if in_method:
            if cond_label_pattern.search(line):
                new_lines.append(line)
                continue

            if ".locals" in line:
                new_lines.append(line)
                new_lines.extend(new_codes)
            else:
                new_lines.append(line)

            if ".end method" in line:
                in_method = False

            continue

        new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        print(f"{YELLOW}WARN: {NC}Method {method_name} not found in the file.")
        sys.exit(1)


def create_delcopy_method(file_path):
    method_name = "public setTextAndCheck2(Ljava/lang/CharSequence;ZZ)V"
    copy_method(
        file_path,
        "public setTextAndCheck(Ljava/lang/CharSequence;ZZ)V",
        method_name,
    )
    with open(file_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    in_method = False
    method_found = False
    cond_label_pattern = re.compile(r":cond_\d")
    new_codes = [
        "    invoke-virtual {p0}, Landroid/view/View;->getContext()Landroid/content/Context;\n",
        "    move-result-object v1\n",
        '    const-string v0, "Turned off"\n',
        "    if-eqz p2, :cond_48\n",
        '    const-string v0, "Turned on"\n',
        "    :cond_48\n",
        "    invoke-static {v1, v0, v2}, Landroid/widget/Toast;->makeText(Landroid/content/Context;Ljava/lang/CharSequence;I)Landroid/widget/Toast;\n",
        "    move-result-object v0\n",
        "    invoke-virtual {v0}, Landroid/widget/Toast;->show()V\n",
        "    if-eqz p2, :cond_55\n",
        "    invoke-static {}, Lorg/telegram/abhi/Hook;->hook()V\n",
        "    goto :goto_58\n",
        "    :cond_55\n",
        "    invoke-static {}, Lorg/telegram/abhi/Hook;->unhook()V\n",
        "    :goto_58\n",
        "    return-void\n",
    ]

    for line in lines:
        if f".method {method_name}" in line:
            in_method = True
            method_found = True
            new_lines.append(line)
            continue

        if in_method:
            if cond_label_pattern.search(line):
                new_lines.append(line)
                continue

            if "return-void" in line:
                new_lines.extend(new_codes)
            else:
                new_lines.append(line)

            if ".end method" in line:
                in_method = False

            continue

        new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        print(f"{YELLOW}WARN: {NC}Method {method_name} not found in the file.")
        sys.exit(1)


def modify_isPremium_stories(file_path):
    """Modify isPremium method in StoriesController.
    - This is different from simple isPremium method.
    It's for Stories related checks
    """
    new_method_code = [
        ".method private isPremium(J)Z\n",
        "    .locals 1\n",
        "    const/4 p1, 0x1\n",
        "    return p1\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "private isPremium(J)Z", new_method_code)
    except NoMethodFoundError:
        # Maybe plus messenger ? let's look for 2nd method
        new_method_code = [
            ".method public final isPremium(J)Z\n",
            "    .locals 1\n",
            "    const/4 p1, 0x1\n",
            "    return p1\n",
            ".end method\n",
        ]
        try:
            modify_method(file_path, "public final isPremium(J)Z", new_method_code)
        except NoMethodFoundError:
            print(f"{YELLOW}No isPremium(J)Z method found in StoriesController!{NC}")


def modify_getCertificateSHA256Fingerprint(file_path):
    """Modify getCertificateSHA256Fingerprint method.
    - In Telegram [Official] this change is very important
    because it allows you to use the app without any restrictions.
    else you'll not even be able to login into the app
    if somehow you does then you account may get at risk
    """
    new_method_code = [
        ".method public static getCertificateSHA256Fingerprint()Ljava/lang/String;\n",
        "    .locals 1\n",
        '    const-string v0, "49C1522548EBACD46CE322B6FD47F6092BB745D0F88082145CAF35E14DCC38E1"\n',
        "    return-object v0\n",
        ".end method\n",
    ]
    try:
        modify_method(
            file_path,
            "public static getCertificateSHA256Fingerprint()Ljava/lang/String;",
            new_method_code,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_forcePremium(file_path):
    """Modify forcePremium method to true.
    - Though this change feels useless to me most of the time
    """
    new_method_code = [
        ".method static synthetic access$3000(Lorg/telegram/ui/PremiumPreviewFragment;)Z\n",
        "    .locals 0\n",
        "    const/4 p0, 0x1\n",
        "    return p0\n",
        ".end method\n",
    ]
    try:
        modify_method(
            file_path,
            "static synthetic access$3000(Lorg/telegram/ui/PremiumPreviewFragment;)Z",
            new_method_code,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_markStories_method(file_path):
    """Modify markStoryAsRead methods
    - Allows users to 'hide their views' to watched stories
    """
    new_method_code1 = [
        ".method public markStoryAsRead(Lorg/telegram/tgnet/tl/TL_stories$PeerStories;Lorg/telegram/tgnet/tl/TL_stories$StoryItem;Z)Z\n",
        "    .locals 1\n",
        "    const/4 v0, 0x0\n",
        "    return v0\n",
        ".end method\n",
    ]
    new_method_code2 = [
        ".method public markStoryAsRead(JLorg/telegram/tgnet/tl/TL_stories$StoryItem;)Z\n",
        "    .locals 2\n",
        "    const/4 p1, 0x0\n",
        "    return p1\n",
        ".end method\n",
    ]
    try:
        modify_method(
            file_path,
            "public markStoryAsRead(Lorg/telegram/tgnet/tl/TL_stories$PeerStories;Lorg/telegram/tgnet/tl/TL_stories$StoryItem;Z)Z",
            new_method_code1,
        )
    except NoMethodFoundError as e:
        print(e)
    try:
        modify_method(
            file_path,
            "public markStoryAsRead(JLorg/telegram/tgnet/tl/TL_stories$StoryItem;)Z",
            new_method_code2,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_isPremiumFeatureAvailable_method(file_path, method_name):
    """Modify isPremiumFeatureAvailable method to change 'const/4 v1, 0x0' to 'const/4 v1, 0x1'."""
    with open(file_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    in_method = False
    method_found = False
    cond_label_pattern = re.compile(r":cond_\d")

    for line in lines:
        if f".method {method_name}" in line:
            in_method = True
            method_found = True
            new_lines.append(line)
            continue

        if in_method:
            if cond_label_pattern.search(line):
                new_lines.append(line)
                continue

            if "const/4 v1, 0x0" in line:
                new_lines.append("    const/4 v1, 0x1\n")
            else:
                new_lines.append(line)

            if ".end method" in line:
                in_method = False

            continue

        new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        print(f"{YELLOW}WARN: {NC}Method {method_name} not found in the file.")


def modify_secret_media_methods(file_path):
    """Modify given methods in MessageObject.smali for Secret Media Enabler.
    - This allows users to view secret media without worrying about their destruction or timeout.
    """
    with open(file_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    in_method = False
    method_found = {
        "public getSecretTimeLeft()I": False,
        "public isSecretMedia()Z": False,
        "public static isSecretPhotoOrVideo(Lorg/telegram/tgnet/TLRPC$Message;)Z": False,
        "public static isSecretMedia(Lorg/telegram/tgnet/TLRPC$Message;)Z": False,
    }
    method_codes = {
        "public isSecretMedia()Z": [
            ".method public isSecretMedia()Z\n",
            "    .locals 5\n",
            "    .line 0\n",
            "    iget-object v0, p0, Lorg/telegram/messenger/MessageObject;->messageOwner:Lorg/telegram/tgnet/TLRPC$Message;\n",
            "    instance-of v1, v0, Lorg/telegram/tgnet/TLRPC$TL_message_secret;\n",
            "    const/4 v3, 0x0\n",
            "    return v3\n",
            ".end method\n",
        ],
        "public static isSecretPhotoOrVideo(Lorg/telegram/tgnet/TLRPC$Message;)Z": [
            ".method public static isSecretPhotoOrVideo(Lorg/telegram/tgnet/TLRPC$Message;)Z\n",
            "    .locals 4\n",
            "    instance-of v0, p0, Lorg/telegram/tgnet/TLRPC$TL_message_secret;\n",
            "    const/4 v2, 0x0\n",
            "    return v2\n",
            ".end method\n",
        ],
        "public static isSecretMedia(Lorg/telegram/tgnet/TLRPC$Message;)Z": [
            ".method public static isSecretMedia(Lorg/telegram/tgnet/TLRPC$Message;)Z\n",
            "    .locals 4\n",
            "    .line 0\n",
            "    instance-of v0, p0, Lorg/telegram/tgnet/TLRPC$TL_message_secret;\n",
            "    const/4 v2, 0x0\n",
            "    return v2\n",
            ".end method\n",
        ],
    }

    for line in lines:
        if any(method_name in line for method_name in method_found.keys()):
            in_method = True
            method_name = next(
                method_name
                for method_name in method_found.keys()
                if method_name in line
            )
            method_found[method_name] = True
            if method_name == "public getSecretTimeLeft()I":
                new_lines.append(line)
                continue
            else:
                new_lines.extend(method_codes[method_name])
                continue

        if in_method:
            if method_name == "public getSecretTimeLeft()I":
                if "const/4 v1, 0x0" in line:
                    new_lines.append("    const/4 v1, 0x1\n")
                    print(
                        f"{GREEN}INFO: {NC}Modified const/4 v1, 0x0 to const/4 v1, 0x1 in getSecretTimeLeft method."
                    )
                else:
                    new_lines.append(line)

            if ".end method" in line:
                in_method = False
            continue

        new_lines.append(line)

    if all(method_found.values()):
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Secret Media methods modified successfully.")
    else:
        print(f"{YELLOW}WARN: {NC}Some Secret Media methods not found in the file.")


def modify_updateParams_method(file_path, method_name):
    """Modify updateParams method for faster downloads"""
    with open(file_path, "r") as file:
        lines = file.readlines()

    new_lines = []
    in_method = False
    method_found = False
    cond_label_pattern = re.compile(r":cond_\d")

    for line in lines:
        if f".method {method_name}" in line:
            in_method = True
            method_found = True
            new_lines.append(line)
            continue

        if in_method:
            if cond_label_pattern.search(line):
                new_lines.append(line)
                continue

            if "const/high16 v0, 0x20000" in line:
                new_lines.append("    const/high16 v0, 0x80000\n")
            elif "const/4 v0, 0x4" in line:
                new_lines.append("    const/16 v0, 0x8\n")
            else:
                new_lines.append(line)

            if ".end method" in line:
                in_method = False

            continue

        new_lines.append(line)

    if method_found:
        with open(file_path, "w") as file:
            file.writelines(new_lines)
        print(f"{GREEN}INFO: {NC}Method {method_name} modified successfully.")
    else:
        print(f"{YELLOW}WARN: {NC}Method {method_name} not found in the file.")


# ONly apply below one in Plus Messenger, Telegram will crash if you do so
# def modify_markAsReadStories(file_path):
#     """Modify the smali file to change the iget-boolean and if-nez lines."""
#     with open(file_path, "r") as file:
#         lines = file.readlines()

#     new_lines = []
#     in_method = False
#     method_found = False
#     cond_label_pattern = re.compile(r":cond_\d")
#     register_pattern = re.compile(r"v\d+")

#     for line in lines:
#         if (
#             "iget-boolean" in line
#             and "Lorg/telegram/tgnet/TLRPC$User;->premium:Z" in line
#         ):
#             method_found = True
#             new_lines.append(line)
#             new_lines.append("    const/4 v9, 0x1\n")
#         elif "if-nez" in line and cond_label_pattern.search(line):
#             new_lines.append(line)
#         else:
#             new_lines.append(line)


#         # if method_found:
#         #     with open(file_path, "w") as file:
#         #         file.writelines(new_lines)
#         #     new_method_code = [
#         #         ".method private updateButton(Z)V\n",
#         #         ".locals 5\n",
#         #         "const/4 v0, 0x0\n",
#         #         "const/4 v2, 0x1\n",
#         #         "iput-boolean v2, p0, Lorg/telegram/ui/Stories/StealthModeAlert;->stealthModeIsActive:Z\n",
#         #         "iget-object v0, p0, Lorg/telegram/ui/Stories/StealthModeAlert;->button:Lorg/telegram/ui/Components/Premium/PremiumButtonView;\n",
#         #         "sget v1, Lorg/telegram/messenger/R$string;->StealthModeIsActive:I\n",
#         #         "invoke-static {v1}, Lorg/telegram/messenger/LocaleController;->getString(I)Ljava/lang/String;\n",
#         #         "move-result-object v1\n",
#         #         "invoke-virtual {v0, v1, v2, p1}, Lorg/telegram/ui/Components/Premium/PremiumButtonView;->setOverlayText(Ljava/lang/String;ZZ)V\n",
#         #         "iget-object p1, p0, Lorg/telegram/ui/Stories/StealthModeAlert;->button:Lorg/telegram/ui/Components/Premium/PremiumButtonView;\n",
#         #         "iget-object p1, p1, Lorg/telegram/ui/Components/Premium/PremiumButtonView;->overlayTextView:Lorg/telegram/ui/Components/AnimatedTextView;\n",
#         #         "sget v0, Lorg/telegram/ui/ActionBar/Theme;->key_featuredStickers_buttonText:I\n",
#         #         "invoke-static {v0}, Lorg/telegram/ui/ActionBar/Theme;->getColor(I)I\n",
#         #         "move-result v0\n",
#         #         "invoke-virtual {p1, v0}, Lorg/telegram/ui/Components/AnimatedTextView;->setTextColor(I)V\n",
#         #         "return-void\n",
#         #         ".end method\n",
#         #     ]
#         # modify_method(file_path, "private updateButton(Z)V", new_method_code)
#         print(
#             f"{GREEN}INFO: {NC}MarkAsRead patch applied successfully."
#         )
#     else:
#         print(
#             f"{YELLOW}WARN: {NC}MarkAsRead patch not found in the file."
#         )


def modify_isChatNoForwards(file_path):
    """Saving Media From Forward Restricted Group/Channels"""
    new_method_code1 = [
        ".method public isChatNoForwards(J)Z\n",
        "    .registers 3\n",
        "    const/4 p1, 0x0\n",
        "    return p1\n",
        ".end method\n",
    ]
    new_method_code2 = [
        ".method public isChatNoForwards(Lorg/telegram/tgnet/TLRPC$Chat;)Z\n",
        "    .registers 4\n",
        "    const/4 p1, 0x0\n",
        "    return p1\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "public isChatNoForwards(J)Z", new_method_code1)
    except NoMethodFoundError as e:
        print(e)
    try:
        modify_method(
            file_path,
            "public isChatNoForwards(Lorg/telegram/tgnet/TLRPC$Chat;)Z",
            new_method_code2,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_checkCanOpenChat(file_path):
    """Access Banned Channels [Main]"""
    new_method_code1 = [
        ".method public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;)Z\n",
        "    .registers 3\n",
        "    const/4 p1, 0x1\n",
        "    return p1\n",
        ".end method\n",
    ]
    new_method_code2 = [
        ".method public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;Lorg/telegram/messenger/MessageObject;)Z\n",
        "    .registers 4\n",
        "    const/4 p1, 0x1\n",
        "    return p1\n",
        ".end method\n",
    ]
    new_method_code3 = [
        ".method public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;Lorg/telegram/messenger/MessageObject;Lorg/telegram/messenger/browser/Browser$Progress;)Z\n",
        "    .registers 5\n",
        "    const/4 p1, 0x1\n",
        "    return p1\n",
        ".end method\n",
    ]
    try:
        modify_method(
            file_path,
            "public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;)Z",
            new_method_code1,
        )
    except NoMethodFoundError as e:
        print(e)
    try:
        modify_method(
            file_path,
            "public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;Lorg/telegram/messenger/MessageObject;)Z",
            new_method_code2,
        )
    except NoMethodFoundError as e:
        print(e)
    try:
        modify_method(
            file_path,
            "public checkCanOpenChat(Landroid/os/Bundle;Lorg/telegram/ui/ActionBar/BaseFragment;Lorg/telegram/messenger/MessageObject;Lorg/telegram/messenger/browser/Browser$Progress;)Z",
            new_method_code3,
        )
    except NoMethodFoundError as e:
        print(e)


def modify_is_sponsored_method(file_path):
    """Disable isSponsored Check"""
    new_method_code = [
        ".method public isSponsored()Z\n",
        "    .locals 2\n",
        "    const/4 v0, 0x0\n",
        "    return v0\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "public isSponsored()Z", new_method_code)
    except NoMethodFoundError as e:
        print(e)


def modify_is_sponsored_dis_method(file_path):
    """Force isSponsoredDisabled True"""
    new_method_code = [
        ".method public isSponsoredDisabled()Z\n",
        "    .locals 2\n",
        "    const/4 v0, 0x1\n",
        "    return v0\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "public isSponsoredDisabled()Z", new_method_code)
    except NoMethodFoundError as e:
        print(e)


def modify_is_proxy_sponsored_method(file_path):
    """Remove Proxy Sponsored Channels"""
    new_method_code = [
        ".method private checkPromoInfoInternal(Z)V\n",
        ".locals 2\n",
        "return-void\n",
        ".end method\n",
    ]
    try:
        modify_method(file_path, "private checkPromoInfoInternal(Z)V", new_method_code)
    except NoMethodFoundError as e:
        print(e)


def automate_modification(root_directory, target_file, modification_function):
    """Automate the process of finding the 'relevant smali file' and applying the modification."""
    smali_file_path = find_smali_file(root_directory, target_file)

    if smali_file_path:
        print(f"{GREEN}INFO: {NC}Found {target_file} at: {smali_file_path}")
        modification_function(smali_file_path)
    else:
        print(f"{YELLOW}WARN: {NC}{target_file} not found in {root_directory}.")


def automate_method_modification(root_directory, method_name, modification_function):
    """Automate the process of finding the 'method in smali files' and applying the modification."""
    smali_file_path = find_smali_file_by_method(root_directory, method_name)

    if smali_file_path:
        print(f"{GREEN}INFO: {NC}Found the method in file: {smali_file_path}")
        modification_function(smali_file_path, method_name)
    else:
        print(
            f"{YELLOW}WARN: {NC}Method {method_name} not found in any file under {root_directory}."
        )


def apply_patches(patches, exclude=None):
    """Apply all patches except the ones specified in the exclude list."""
    for key, value in patches.items():
        if key not in exclude:
            value[1]()


def main(selected_patch=None, root_directory=None):
    """Main function to handle user input and apply patches."""

    if root_directory == "Telegram":
        root_directory = (
            input("Give me the decompiled directory path (Default is 'Telegram'): ")
            or root_directory
        )

    patches = {
        "0": (
            f"{BLUE}Apply all patches [Except Anti Messages Delete Patch]{NC}",
            lambda: apply_patches(patches, exclude=["0", "00", "17"]),
        ),
        "00": (
            f"{BLUE}Apply all patches [Including Anti Messages Delete Patch]{NC}",
            lambda: apply_patches(patches, exclude=["0", "00"]),
        ),
        "1": (
            f"Disable Signature Verification {YELLOW}(Must for Telegram){NC}",
            lambda: automate_modification(
                root_directory,
                "AndroidUtilities.smali",
                modify_getCertificateSHA256Fingerprint,
            ),
        ),
        "2": (
            "Modify isPremium method to true",
            lambda: automate_modification(
                root_directory, "UserConfig.smali", modify_isPremium
            ),
        ),
        "3": (
            "Modify isPremium method for Stories to true",
            lambda: automate_modification(
                root_directory, "StoriesController.smali", modify_isPremium_stories
            ),
        ),
        "4": (
            "Modify forcePremium method to true",
            lambda: automate_modification(
                root_directory, "PremiumPreviewFragment.smali", modify_forcePremium
            ),
        ),
        "5": (
            "Modify markStoryAsRead methods to disable marking stories as read",
            lambda: automate_modification(
                root_directory, "StoriesController.smali", modify_markStories_method
            ),
        ),
        "6": (
            "Modify isPremiumFeatureAvailable method to true",
            lambda: automate_method_modification(
                root_directory,
                "private isPremiumFeatureAvailable(I)Z",
                modify_isPremiumFeatureAvailable_method,
            )
            or automate_method_modification(
                root_directory,
                "public final isPremiumFeatureAvailable(I)Z",
                modify_isPremiumFeatureAvailable_method,
            ),
        ),
        "7": (
            "Modify updateParams method for speed boost",
            lambda: automate_method_modification(
                root_directory, "private updateParams()V", modify_updateParams_method
            ),
        ),
        "8": (
            "Modify isChatNoForwards methods in MessagesController.smali",
            lambda: automate_modification(
                root_directory,
                "MessagesController.smali",
                modify_isChatNoForwards,
            ),
        ),
        "9": (
            "Access Banned Channels Patch: Modify checkCanOpenChat methods",
            lambda: automate_modification(
                root_directory,
                "MessagesController.smali",
                modify_checkCanOpenChat,
            ),
        ),
        "10": (
            "Access Banned Channels: Apply isRestrictedMessage patch",
            lambda: apply_isRestrictedMessage(root_directory),
        ),
        "11": (
            "Apply enableSavingMedia patch",
            lambda: apply_enableSavingMedia(root_directory),
        ),
        "12": (
            "Apply premiumLocked patch",
            lambda: apply_premiumLocked(root_directory),
        ),
        "13": (
            "Enable Screenshots",
            lambda: (
                apply_EnableScreenshots(root_directory),
                apply_EnableScreenshots2(root_directory),
                apply_EnableScreenshots3(root_directory),
            ),
        ),
        "14": (
            "Modify isSponsored method to always return false",
            lambda: automate_modification(
                root_directory, "MessageObject.smali", modify_is_sponsored_method
            ),
        ),
        "15": (
            "Remove Proxy Sponsored Channels",
            lambda: automate_modification(
                root_directory,
                "MessagesController.smali",
                modify_is_proxy_sponsored_method,
            ),
        ),
        "16": (
            "Modify Secret Media methods (for Secret Media Enabler)",
            lambda: automate_modification(
                root_directory, "MessageObject.smali", modify_secret_media_methods
            ),
        ),
        "17": (
            "Apply Anti Messages Delete Patch",
            lambda: automate_modification(
                root_directory, "MessagesStorage.smali", modify_markMessagesAsDeleted
            ),
        ),
        "18": (
            "Modify isSponsoredDisabled to always return true",
            lambda: automate_modification(
                root_directory, "MessagesController.smali", modify_is_sponsored_dis_method
            ),
        ),
    }

    if not selected_patch:
        print("Select patches to apply (comma-separated):")
        for key, (description, _) in patches.items():
            print(f"{key}: {description}")

        selected_patches = input("Enter patch numbers: ").split(",")
        selected_patches = [patch.strip() for patch in selected_patches]
    else:
        selected_patches = [selected_patch]

    for patch in selected_patches:
        if patch in patches:
            print(
                f"{YELLOW}START: {NC}Applying patch {patch}: {BLUE}{patches[patch][0]}{NC}"
            )
            patches[patch][1]()
        else:
            print(f"{RED}ERROR: {NC}Invalid patch number: {patch}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="tgpatcher", description="Telegram Patches (Mod) Applier"
    )

    parser.add_argument(
        "--normal",
        help="Normal Mod Patches",
        required=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--anti",
        help="Normal + Anti Mod Patches",
        required=False,
        action=argparse.BooleanOptionalAction,
    )
    parser.add_argument(
        "--dir", help="Specify the directory", required=False, default="Telegram"
    )

    args = parser.parse_args()

    try:
        if args.normal:
            main(selected_patch="0", root_directory=args.dir)
        elif args.anti:
            main(selected_patch="00", root_directory=args.dir)
        else:
            main(root_directory=args.dir)
    except KeyboardInterrupt:
        print(f"\n{RED}ERROR: {NC}Script interrupted by user.")
        sys.exit(1)
