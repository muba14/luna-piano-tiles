.class final Lcom/lunapiano/tiles/MainActivity$BackCb;
.super Ljava/lang/Object;
.implements Landroid/webkit/ValueCallback;

.field final act:Lcom/lunapiano/tiles/MainActivity;

.method constructor <init>(Lcom/lunapiano/tiles/MainActivity;)V
    .locals 0
    invoke-direct {p0}, Ljava/lang/Object;-><init>()V
    iput-object p1, p0, Lcom/lunapiano/tiles/MainActivity$BackCb;->act:Lcom/lunapiano/tiles/MainActivity;
    return-void
.end method

.method public onReceiveValue(Ljava/lang/Object;)V
    .locals 2
    const-string v0, "\"exit\""
    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z
    move-result v0
    if-eqz v0, :done
    iget-object v1, p0, Lcom/lunapiano/tiles/MainActivity$BackCb;->act:Lcom/lunapiano/tiles/MainActivity;
    invoke-virtual {v1}, Lcom/lunapiano/tiles/MainActivity;->finish()V
    :done
    return-void
.end method
