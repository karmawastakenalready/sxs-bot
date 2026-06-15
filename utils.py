import discord
import database

def has_permission(interaction: discord.Interaction, required_perm: str) -> bool:
    if interaction.permissions.administrator:
        return True
        
    conn = database.get_connection()
    cursor = conn.cursor()
    
    user_roles = [str(r.id) for r in interaction.user.roles]
    if not user_roles:
        conn.close()
        return False
        
    placeholders = ','.join('?' for _ in user_roles)
    query = f'''
        SELECT 1 FROM role_permissions 
        WHERE guild_id = ? AND permission = ? AND role_id IN ({placeholders})
    '''
    params = [str(interaction.guild_id), required_perm] + user_roles
    cursor.execute(query, params)
    result = cursor.fetchone()
    conn.close()
    
    return result is not None
